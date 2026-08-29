"""
Main Graph für das DACH Startup Matchmaker & Pitch Agent System.

Orchestriert die 5 Agenten (Scout, Profiler, Matchmaker, Pitch Architect, Profile Updater)
als Nodes in einem LangGraph StateGraph mit bedingten Kanten und Feedback-Loop.
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from state import AgentState
from agents.scout import scout_node
from agents.profiler import profiler_node
from agents.matchmaker import matchmaker_node
from agents.pitch_architect import pitch_architect_node
from agents.profile_updater import profile_updater_node
from tools.obsidian_writer import ensure_obsidian_structure, read_from_obsidian, save_to_obsidian

load_dotenv()

# Temporäre Speicher für States bei Feedback-Warteschleife
TEMP_STATE_DIR = Path("./.temp_states")
TEMP_STATE_DIR.mkdir(parents=True, exist_ok=True)


def should_continue(state: AgentState) -> str:
    """
    Bedingte Kante: Entscheidet über den nächsten Schritt nach dem Matchmaker.
    
    Returns:
        "profile_updater" wenn user_feedback vorhanden ist
        "pitch_architect" wenn fit_score >= 70
        "wait_for_feedback" wenn fit_score < 70 und kein Feedback
    """
    # Prüfen ob User-Feedback vorhanden ist → dann zuerst Profil updaten
    if state.get("user_feedback"):
        return "profile_updater"
    elif state.get("fit_score", 0) >= 70:
        return "pitch_architect"
    else:
        return "wait_for_feedback"


def wait_for_feedback_node(state: AgentState) -> AgentState:
    """
    Placeholder Node: Wartet auf User-Feedback wenn Fit-Score zu niedrig.
    
    Speichert den aktuellen State temporär für späteres Resume.
    """
    startup_name = state["startup_name"]
    print(f"⏸️  Fit-Score ({state['fit_score']}) unter 70. Warte auf Feedback...")
    
    # State temporär speichern für späteres Resume
    temp_state_file = TEMP_STATE_DIR / f"{startup_name.replace(' ', '_')}.json"
    with open(temp_state_file, 'w', encoding='utf-8') as f:
        # Serialisiere State (ohne nicht-serialisierbare Objekte)
        serializable_state = {
            "startup_name": state["startup_name"],
            "raw_data": state["raw_data"],
            "culture_profile": state["culture_profile"],
            "fit_score": state["fit_score"],
            "fit_reasoning": state["fit_reasoning"],
            "user_feedback": state.get("user_feedback"),
            "pitch_draft": state.get("pitch_draft"),
            "obsidian_paths": state["obsidian_paths"]
        }
        json.dump(serializable_state, f, indent=2, ensure_ascii=False)
    
    print(f"💾 State gespeichert in: {temp_state_file}")
    print("\nNächste Schritte:")
    print("1. Öffne match-analysis.md in Obsidian")
    print("2. Füge im Abschnitt '## Dein Feedback' deine Kommentare hinzu")
    print("3. Führe aus: python main.py --startup \"" + startup_name + "\" --feedback \"Dein Feedback hier\"")
    
    return state


def build_graph() -> StateGraph:
    """
    Baut den LangGraph StateGraph mit allen Nodes und Kanten.
    
    Flow:
        START → scout → profiler → matchmaker → [conditional]
                                                      ↓
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    ↓                                 ↓                                 ↓
            profile_updater                   pitch_architect                 wait_for_feedback
                    ↓                                 ↓                                 ↓
                matchmaker                         END                               END
    """
    # Initialisiere Graph mit AgentState
    workflow = StateGraph(AgentState)
    
    # Füge alle Nodes hinzu
    workflow.add_node("scout", scout_node)
    workflow.add_node("profiler", profiler_node)
    workflow.add_node("matchmaker", matchmaker_node)
    workflow.add_node("pitch_architect", pitch_architect_node)
    workflow.add_node("profile_updater", profile_updater_node)
    workflow.add_node("wait_for_feedback", wait_for_feedback_node)
    
    # Definiere Startpunkt
    workflow.set_entry_point("scout")
    
    # Lineare Kanten: scout → profiler → matchmaker
    workflow.add_edge("scout", "profiler")
    workflow.add_edge("profiler", "matchmaker")
    
    # Bedingte Kante nach matchmaker
    workflow.add_conditional_edges(
        "matchmaker",
        should_continue,
        {
            "profile_updater": "profile_updater",
            "pitch_architect": "pitch_architect",
            "wait_for_feedback": "wait_for_feedback"
        }
    )
    
    # Loop zurück von profile_updater zu matchmaker (für Re-Matching)
    workflow.add_edge("profile_updater", "matchmaker")
    
    # Beide End-Nodes führen zu END
    workflow.add_edge("pitch_architect", END)
    workflow.add_edge("wait_for_feedback", END)
    
    # Kompiliere Graph
    app = workflow.compile()
    return app


def run_startup_screening(startup_name: str, founder_names: Optional[List[str]] = None) -> None:
    """
    Führt das komplette Screening für ein Startup durch.
    
    1. Initialisiere State mit startup_name
    2. Lade OBSIDIAN_VAULT_PATH aus .env
    3. Erstelle Obsidian-Struktur
    4. Invoke den Graph
    5. Wenn fit_score < 70 und kein Feedback:
       - Drucke Nachricht: "Bitte öffne match-analysis.md in Obsidian und füge Feedback hinzu"
       - Speichere State in temporäre Datei
    
    Args:
        startup_name: Name des Startups
        founder_names: Optionale Liste von Gründer-Namen (User-Override)
    """
    # Baue Graph
    app = build_graph()
    
    # Lade Obsidian Vault Path
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")
    print(f"📁 Obsidian Vault: {vault_path}")
    
    # Erstelle Obsidian-Struktur
    obsidian_paths = ensure_obsidian_structure(vault_path, startup_name)
    print(f"📂 Ordnerstruktur erstellt für: {startup_name}")
    
    # Initialisiere State
    initial_state: AgentState = {
        "startup_name": startup_name,
        "founder_names": founder_names,
        "founder_info": None,
        "raw_data": {},
        "culture_profile": {},
        "fit_score": 0,
        "fit_reasoning": "",
        "user_feedback": None,
        "pitch_draft": None,
        "obsidian_paths": obsidian_paths
    }
    
    # Führe Graph aus
    print(f"\n🚀 Starte Analyse für: {startup_name}")
    print("="*60)
    result = app.invoke(initial_state)
    
    # Ergebnis anzeigen
    print("\n" + "="*60)
    print("Ergebnis:")
    print(f"Fit-Score: {result['fit_score']}/100")
    
    if result['fit_score'] >= 80:
        emoji = "🎯"
    elif result['fit_score'] >= 70:
        emoji = "✅"
    elif result['fit_score'] >= 50:
        emoji = "⚠️"
    else:
        emoji = "❌"
    
    print(f"Bewertung: {emoji}")
    print(f"\nBegründung:\n{result['fit_reasoning']}")
    
    if result.get('pitch_draft'):
        print("\n" + "="*60)
        print("📧 Pitch Draft generiert!")
        print(f"Öffne: {obsidian_paths['pitch_proposal']}")
    
    print("\n" + "="*60)
    print(f"📄 Alle Dateien in Obsidian: {vault_path}/startup-screening/startups/{startup_name}/")


def resume_with_feedback(startup_name: str, feedback: str) -> None:
    """
    Setzt das Screening mit User-Feedback fort.
    
    1. Lade gespeicherten State aus temporärer Datei
    2. Füge feedback hinzu
    3. Resume den Graph ab profile_updater
    
    Args:
        startup_name: Name des Startups
        feedback: User-Feedback zur Match-Analyse
    """
    # Baue Graph
    app = build_graph()
    
    # Lade gespeicherten State
    temp_state_file = TEMP_STATE_DIR / f"{startup_name.replace(' ', '_')}.json"
    
    if not temp_state_file.exists():
        print(f"❌ Kein gespeicherter State gefunden für: {startup_name}")
        print("Führe zuerst 'python main.py --startup \"{startup_name}\"' aus.")
        return
    
    # Lade State aus JSON
    with open(temp_state_file, 'r', encoding='utf-8') as f:
        saved_state = json.load(f)
    
    # Füge Feedback hinzu
    saved_state["user_feedback"] = feedback
    
    # Lade Obsidian Vault Path
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")
    saved_state["obsidian_paths"] = ensure_obsidian_structure(vault_path, startup_name)
    
    print(f"🔄 Setze Analyse fort für: {startup_name}")
    print(f"💬 Feedback: {feedback[:100]}...")
    print("="*60)
    
    # Resume Graph (wird automatisch bei profile_updater starten wegen user_feedback)
    result = app.invoke(saved_state)
    
    # Ergebnis anzeigen
    print("\n" + "="*60)
    print("Neues Ergebnis nach Feedback-Verarbeitung:")
    print(f"Fit-Score: {result['fit_score']}/100")
    
    if result['fit_score'] >= 80:
        emoji = "🎯"
    elif result['fit_score'] >= 70:
        emoji = "✅"
    elif result['fit_score'] >= 50:
        emoji = "⚠️"
    else:
        emoji = "❌"
    
    print(f"Bewertung: {emoji}")
    print(f"\nBegründung:\n{result['fit_reasoning']}")
    
    if result.get('pitch_draft'):
        print("\n" + "="*60)
        print("📧 Pitch Draft generiert!")
        print(f"Öffne: {result['obsidian_paths']['pitch_proposal']}")
    
    print("\n" + "="*60)
    print("✅ Profil wurde aktualisiert basierend auf deinem Feedback!")
    print(f"📄 Neues Profil: {result['obsidian_paths']['profile']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DACH Startup Matchmaker & Pitch Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py --startup "n8n"
  python main.py --startup "DeepL" --feedback "Remote-First ist mir wichtiger als gedacht"
        """
    )
    parser.add_argument(
        "--startup", 
        type=str, 
        required=True, 
        help="Name des Startups (z.B. 'n8n', 'DeepL', 'Personio')"
    )
    parser.add_argument(
        "--feedback", 
        type=str, 
        default=None, 
        help="User-Feedback zur Match-Analyse (optional)"
    )
    parser.add_argument(
        "--founder", 
        type=str, 
        default=None, 
        help="Gründer-Namen (kommagetrennt), z.B. 'Jan Oberhauser,David Fankhauser'"
    )
    args = parser.parse_args()
    
    if args.feedback:
        resume_with_feedback(args.startup, args.feedback)
    else:
        run_startup_screening(args.startup, founder_names=args.founder.split(",") if args.founder else None)
