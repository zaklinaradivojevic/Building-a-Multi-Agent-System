# Čitamo URL-ove mikroservisa iz okruženja (koje postavlja run_local.sh ili .env)
RESEARCHER_URL = os.getenv("RESEARCHER_AGENT_CARD_URL", "http://localhost:8001/a2a/agent/.well-known/agent.json")
JUDGE_URL = os.getenv("JUDGE_AGENT_CARD_URL", "http://localhost:8002/a2a/agent/.well-known/agent.json")
CONTENT_BUILDER_URL = os.getenv("CONTENT_BUILDER_AGENT_CARD_URL", "http://localhost:8003/a2a/agent/.well-known/agent.json")

# Pravimo autentifikovani HTTP klijent za sigurnu komunikaciju između agenata
authenticated_client = create_authenticated_client()
import os
import json
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent  # Ispravan import za ADK 2.x
from google.adk import Agent, InvocationContext, CallbackContext
from google.adk.events import Event, EventActions
from authenticated_httpx import create_authenticated_client
# --- Callbacks ---
def create_save_output_callback(key: str):
    """Creates a callback to save the agent's final response to session state."""
    def callback(callback_context: CallbackContext, **kwargs) -> None:
        ctx = callback_context
        # Find the last event from this agent that has content
        for event in reversed(ctx.session.events):
            if event.author == ctx.agent_name and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    # Try to parse as JSON if it looks like it, for judge_feedback
                    if key == "judge_feedback" and text.strip().startswith("{"):
                        try:
                            ctx.state[key] = json.loads(text)
                        except json.JSONDecodeError:
                            ctx.state[key] = text
                    else:
                        ctx.state[key] = text
                    print(f"[{ctx.agent_name}] Saved output to state['{key}']")
                    return
    return callback

# --- Remote Agents ---


# Povezujemo se sa udaljenim mikroservisima preko A2A protokola
researcher_agent = RemoteA2aAgent(
    name="researcher",
    agent_card_url=RESEARCHER_URL,
    client=authenticated_client,
    on_done=create_save_output_callback("research_findings")  # Čuva nalaze u privremeno stanje
)

judge_agent = RemoteA2aAgent(
    name="judge",
    agent_card_url=JUDGE_URL,
    client=authenticated_client,
    on_done=create_save_output_callback("judge_feedback")  # Čuva strukturu {status, feedback}
)

content_builder_agent = RemoteA2aAgent(
    name="content_builder",
    agent_card_url=CONTENT_BUILDER_URL,
    client=authenticated_client,
    on_done=create_save_output_callback("final_course")  # Čuva gotov kurs
)

# --- Escalation Checker ---

class EscalationChecker(BaseAgent):
    """
    Specijalni agent koji ne poziva LLM model, već samo programski proverava 
    da li je Judge dao zeleno svetlo ('pass') kako bi prekinuo petlju (Loop).
    """
    def __init__(self):
        super().__init__(name="escalation_checker")

    async def invoke(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Čitamo fidbek koji je Judge malopre sačuvao u stanje (state)
        judge_feedback = ctx.state.get("judge_feedback", {})
        
        # Ako je fidbek u JSON formatu (rečnik), vadimo 'status'
        if isinstance(judge_feedback, dict):
            status = judge_feedback.get("status", "fail")
        else:
            status = "fail"
            
        print(f"[EscalationChecker] Trenutni status provere istraživanja: {status}")

        if status == "pass":
            # Ako je prošlo, šaljemo ESCALATE događaj koji prekida LoopAgent petlju
            yield Event(
                action=EventActions.ESCALATE, 
                content="Istraživanje je uspešno prošlo proveru. Prelazimo na kreiranje kursa."
            )
        else:
            # Ako je fail, nastavljamo petlju (vraća se na Researcher-a sa komentarom sudije)
            feedback_text = judge_feedback.get("feedback", "Nedovoljno informacija.") if isinstance(judge_feedback, dict) else str(judge_feedback)
            yield Event(
                action=EventActions.CONTINUE,
                content=f"Istraživanje nije prošlo. Sudija kaže: {feedback_text}. Pokušaj ponovo sa boljim fokusom."
            )

# --- Orchestration ---

# KORAK 1: Definišemo istraživačku petlju (Researcher -> Judge -> EscalationChecker)
# LoopAgent će vrteti ove agente u krug sve dok EscalationChecker ne baci ESCALATE
research_loop = LoopAgent(
    name="research_loop",
    agents=[researcher_agent, judge_agent, EscalationChecker()]
)

# KORAK 2: Definišemo krovni (Root) Agent Pipeline
# SequentialAgent izvršava stvari hronološki: prvo se završi cela petlja istraživanja,
# a onda se rezultat prosleđuje Content Builder-u za finalni ispis.
root_agent = SequentialAgent(
    name="course_creation_pipeline",
    agents=[research_loop, content_builder_agent]
)

