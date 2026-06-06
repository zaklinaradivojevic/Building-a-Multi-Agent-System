from google.adk.agents import Agent
from google.adk.tools.google_search_tool import google_search

MODEL = "gemini-3-flash-preview"

# KORAK 1: Definisanje Researcher Agent-a sa Google Search alatom
researcher_agent = Agent(
    name="researcher_agent",  # Popravljeno ime
    model=MODEL,
    tools=[google_search],
    instructions=(  # Promenjeno na system_instruction
        "Ti si pedantni i radoznali istraživač, stručnjak za pronalaženje tačnih, "
        "pouzdanih i dubokih informacija na internetu. "
        "Tvoj glavni fokus su istorijske teme, biografije, ključne bitke i filozofski pravci."
    ),
)

@researcher_agent.task
def conduct_research(topic: str) -> str:
    """
    Uzima zadatu temu, pretražuje Google i vraća detaljan istraživački izveštaj.
    """
    prompt = (
        f"Istraži sledeću temu detaljno: '{topic}'\n\n"
        f"Uradi sledeće:\n"
        f"1. Pokreni Google pretragu da pronađeš najrelevantnije informacije.\n"
        f"2. Izvuci ključne istorijske činjenice, datume i aktere.\n"
        f"3. Ako je primenjivo, pronađi važne filozofske misli, citate ili pouke povezane sa temom.\n"
        f"4. Sastavi sve u strukturiran izveštaj (koristi Markdown) koji će biti prosleđen sudiji na proveru."
    )
    
    # Agent će sam prepoznati kada treba da pozove google_search alat tokom generisanja
    response = researcher_agent.generate(prompt)
    return response