import os
from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent, BaseAgent
from google.adk import Context
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

# --- Configuration ---
RESEARCHER_URL = os.getenv("RESEARCHER_AGENT_CARD_URL", "http://localhost:8001")
JUDGE_URL = os.getenv("JUDGE_AGENT_CARD_URL", "http://localhost:8002")
CONTENT_BUILDER_URL = os.getenv("CONTENT_BUILDER_AGENT_CARD_URL", "http://localhost:8003")

# --- Remote Agents (sada bez on_done callback-a) ---
researcher_agent = LlmAgent(
    name="researcher",
    model="gemini-1.5-flash",
    instruction="You are a researcher. Gather comprehensive information about the topic.",
)

judge_agent = LlmAgent(
    name="judge",
    model="gemini-1.5-flash",
    instruction="""You are a judge. Evaluate the research.
    Respond with JSON in this exact format: {"status": "pass" or "fail", "feedback": "your feedback here"}
    Only pass if the research is thorough and complete enough to build a course.""",
)

content_builder_agent = LlmAgent(
    name="content_builder",
    model="gemini-1.5-flash",
    instruction="You are a course builder. Create a comprehensive, detailed course based on the research.",
)

# --- Escalation Checker (isti kao pre, samo bez on_done) ---
class EscalationChecker(BaseAgent):
    """Checks if Judge passed the research."""
    
    def __init__(self):
        super().__init__(name="escalation_checker")

    async def _run_async_impl(self, ctx: Context) -> AsyncGenerator[Event, None]:
        # Pristupi stanju (state) da vidiš da li je judge doneo presudu
        # Ovo je pojednostavljeno - u pravoj aplikaciji bi čitao state
        print(f"[EscalationChecker] Provera statusa...")
        
        # Za sada uvek nastavi petlju
        yield Event(
            author=self.name,
            action=EventActions.CONTINUE,
            content="Continuing research loop."
        )

    async def invoke(self, ctx: Context) -> AsyncGenerator[Event, None]:
        async for event in self._run_async_impl(ctx):
            yield event

# --- Orchestration ---
research_loop = LoopAgent(
    name="research_loop",
    sub_agents=[researcher_agent, judge_agent, EscalationChecker()]
)

root_agent = SequentialAgent(
    name="course_creation_pipeline",
    sub_agents=[research_loop, content_builder_agent]
)