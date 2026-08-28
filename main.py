"""
Main Graph für das DACH Startup Matchmaker & Pitch Agent System.

Orchestriert die 5 Agenten (Scout, Profiler, Matchmaker, Pitch Architect, Profile Updater)
als Nodes in einem LangGraph StateGraph mit bedingten Kanten.
"""

from langgraph.graph import StateGraph, END
from state import AgentState


def scout(state: AgentState) -> AgentState:
    """
    Scout Agent: Sammelt Rohdaten über das Startup.
    
    Quellen: Website, LinkedIn, X/Twitter, GitHub, Podcasts, Interviews, News, Job Postings
    Output: raw_data Dict im State
    """
    print(f"🔍 Scout: Starte Recherche für '{state['startup_name']}'...")
    # TODO: Implementierung folgt in Prompt 2
    state["raw_data"] = {"status": "not_implemented"}
    return state


def profiler(state: AgentState) -> AgentState:
    """
    Profiler Agent: Analysiert Kultur und Werte aus den Rohdaten.
    
    Extrahiert: Philosophie, Werte, Kommunikationsstil, Red/Green Flags
    Output: culture_profile Dict im State
    """
    print("📊 Profiler: Analysiere Unternehmenskultur...")
    # TODO: Implementierung folgt in Prompt 3
    state["culture_profile"] = {"status": "not_implemented"}
    return state


def matchmaker(state: AgentState) -> AgentState:
    """
    Matchmaker Agent: Bewertet Fit zwischen Startup und User-Profil.
    
    Vergleicht culture_profile mit profile.md
    Output: fit_score (0-100), fit_reasoning im State
    """
    print("🎯 Matchmaker: Bewerte Fit...")
    # TODO: Implementierung folgt in Prompt 3
    state["fit_score"] = 0
    state["fit_reasoning"] = "Noch nicht implementiert"
    return state


def pitch_architect(state: AgentState) -> AgentState:
    """
    Pitch Architect Agent: Generiert Door-Opener Projektvorschlag.
    
    Nur wenn fit_score >= 70
    Output: pitch_draft im State
    """
    print("✍️ Pitch Architect: Erstelle Pitch...")
    # TODO: Implementierung folgt in Prompt 3
    state["pitch_draft"] = "Noch nicht implementiert"
    return state


def wait_for_feedback(state: AgentState) -> AgentState:
    """
    Placeholder Node: Wartet auf User-Feedback wenn Fit-Score zu niedrig.
    
    Wird später durch Profile Updater ersetzt.
    """
    print("⏸️  Warte auf User-Feedback...")
    return state


def should_proceed_to_pitch(state: AgentState) -> str:
    """
    Bedingte Kante: Entscheidet ob Pitch generiert wird.
    
    Returns:
        "pitch_architect" wenn fit_score >= 70
        "wait_for_feedback" sonst
    """
    if state.get("fit_score", 0) >= 70:
        return "pitch_architect"
    else:
        return "wait_for_feedback"


def build_graph() -> StateGraph:
    """
    Baut den LangGraph StateGraph mit allen Nodes und Kanten.
    
    Flow:
        START → scout → profiler → matchmaker → [conditional] → pitch_architect/wait_for_feedback → END
    """
    # Initialisiere Graph mit AgentState
    workflow = StateGraph(AgentState)
    
    # Füge alle Nodes hinzu
    workflow.add_node("scout", scout)
    workflow.add_node("profiler", profiler)
    workflow.add_node("matchmaker", matchmaker)
    workflow.add_node("pitch_architect", pitch_architect)
    workflow.add_node("wait_for_feedback", wait_for_feedback)
    
    # Definiere Startpunkt
    workflow.set_entry_point("scout")
    
    # Lineare Kanten: scout → profiler → matchmaker
    workflow.add_edge("scout", "profiler")
    workflow.add_edge("profiler", "matchmaker")
    
    # Bedingte Kante nach matchmaker
    workflow.add_conditional_edges(
        source="matchmaker",
        condition=should_proceed_to_pitch,
        mapping={
            "pitch_architect": "pitch_architect",
            "wait_for_feedback": "wait_for_feedback"
        }
    )
    
    # Beide End-Nodes führen zu END
    workflow.add_edge("pitch_architect", END)
    workflow.add_edge("wait_for_feedback", END)
    
    # Kompiliere Graph
    app = workflow.compile()
    return app


def main():
    """
    Hauptfunktion: Startet den Graph mit einem Beispiel-Startup.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="DACH Startup Matchmaker")
    parser.add_argument("--startup", type=str, required=True, help="Name des Startups")
    parser.add_argument("--feedback", type=str, default=None, help="Optionales Feedback")
    args = parser.parse_args()
    
    # Baue Graph
    app = build_graph()
    
    # Initialisiere State
    initial_state: AgentState = {
        "startup_name": args.startup,
        "raw_data": {},
        "culture_profile": {},
        "fit_score": 0,
        "fit_reasoning": "",
        "user_feedback": args.feedback,
        "pitch_draft": None,
        "obsidian_paths": {}
    }
    
    # Führe Graph aus
    print(f"🚀 Starte Analyse für: {args.startup}")
    result = app.invoke(initial_state)
    
    print("\n" + "="*50)
    print("Ergebnis:")
    print(f"Fit-Score: {result['fit_score']}/100")
    print(f"Begründung: {result['fit_reasoning']}")
    if result['pitch_draft']:
        print(f"\nPitch Draft:\n{result['pitch_draft']}")
    print("="*50)


if __name__ == "__main__":
    main()
