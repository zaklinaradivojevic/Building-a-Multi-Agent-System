from google.adk.agents import Agent

# Koristimo model koji si definisala
MODEL = "gemini-3-flash-preview"

# Definišemo Content Builder Agent-a
content_builder_agent = Agent(
    name="content_builder_agent",  # Popravljeno ime
    model=MODEL,
    instructions=(  # Promenjeno na system_instruction
        "Ti si stručni edukator i kreator online kurseva. "
        "Tvoj zadatak je da uzmeš istraživačke podatke i beleške koje je pripremio Researcher agent, "
        "a koji su prošli proveru i odobrenje od strane Judge agenta, i od njih napraviš "
        "visokokvalitetan, strukturiran i zanimljiv modul kursa."
    ),
)


@content_builder_agent.task
def build_course_module(approved_research: str) -> str:
    """
    Uzima odobreno istraživanje i transformiše ga u finalni modul kursa.
    """
    prompt = (
        f"Na osnovu sledećeg odobrenog istraživanja, kreiraj kompletan i detaljan modul kursa:\n\n"
        f"{approved_research}\n\n"
        f"Struktura modula treba da sadrži:\n"
        f"1. **Naslov modula** (Zanimljiv i privlačan)\n"
        f"2. **Uvod** (Kratak pregled i šta će student naučiti)\n"
        f"3. **Glavne lekcije** (Detaljno razrađene tačke iz istraživanja, sa istorijskim kontekstom, anegdotama i dubljim značenjem)\n"
        f"4. **Ključne poruke/Pouke** (Posebno naglasi filozofske ili praktične pouke, npr. Stoicizam, strategija...)\n"
        f"5. **Rezime i Zaključak**\n\n"
        f"Formatiraj izlaz koristeći čist Markdown sa jasnim naslovima i podnaslovima."
    )
    
    # Pozivamo model da generiše sadržaj na osnovu instrukcija agenta i prompta
    response = content_builder_agent.generate(prompt)
    return response