from typing import Literal
from google.adk.agents import Agent
from google.adk.apps.app import App
from pydantic import BaseModel, Field

MODEL = "gemini-3-flash-preview"

# KORAK 1: Definisanje JudgeFeedback šeme
class JudgeFeedback(BaseModel):
    """
    Struktura odgovora koju Judge agent MORA da vrati nakon evaluacije.
    """
    status: Literal["pass", "fail"] = Field(
        ..., 
        description="Vrati 'pass' ako je istraživanje kompletno i tačno, ili 'fail' ako mu fale ključne informacije ili ima grešaka."
    )
    feedback: str = Field(
        ..., 
        description="Detaljno obrazloženje odluke. Ako je status 'fail', ovde navedi šta tačno treba popraviti ili ponovo istražiti."
    )

# KORAK 2: Definisanje Judge Agent-a
judge_agent = Agent(
    name="judge_agent",  # Popravljeno ime (bez razmaka)
    model=MODEL,
    instructions=(  # Promenjeno sa instructions na system_instruction
        "Ti si strogi ali pravedni istoričar, filozof i kritički ocenjivač sadržaja. "
        "Tvoj zadatak je da pregledaš sirove istraživačke podatke i oceniš njihovu tačnost, "
        "relevantnost, dubinu i istorijski kontekst. "
        "Moraš sprečiti površne informacije, netačne datume ili istorijske zablude da prođu dalje u proces."
    ),
)

@judge_agent.task
def evaluate_research(research_findings: str) -> JudgeFeedback:
    """
    Ocenjuje sakupljeno istraživanje i vraća strukturiran odgovor sa statusom i komentarom.
    """
    prompt = (
        f"Detaljno analiziraj sledeće istraživačke nalaze:\n\n"
        f"{research_findings}\n\n"
        f"Donesi odluku da li je materijal spreman za kreiranje lekcija. "
        f"Proveri istorijsku tačnost, dubinu i da li tema ima smisla. "
        f"Obavezno vrati odgovor u traženom formatu (status i feedback)."
    )
    
    # Pozivamo model, ali koristimo strukturu JudgeFeedback za striktan odgovor
    response = judge_agent.generate(prompt, response_schema=JudgeFeedback)
    return response