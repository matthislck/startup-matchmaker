"""Profile Updater Agent Node - Lernt aus User-Feedback."""

from typing import Dict, Any
from state import AgentState
from tools.obsidian_writer import read_from_obsidian, save_to_obsidian, append_feedback
from config.prompts import PROFILE_UPDATER_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


def profile_updater_node(state: AgentState) -> AgentState:
    """
    Aktualisiert das User-Profil basierend auf Feedback.
    
    1. Lese user_feedback aus state
    2. Lese aktuelle profile.md
    3. Lade PROFILE_UPDATER_PROMPT aus config/prompts.py
    4. Mache LLM-Call:
       - Aktuelles Profil
       - Neues Feedback
       - Ursprüngliche Begründung des Matchmakers
    5. Generiere aktualisiertes Profil
    6. Schreibe neue profile.md
    7. Füge Eintrag zu feedback-log.md hinzu
    
    Returns: Updated state mit neuem Profil
    """
    user_feedback = state.get("user_feedback")
    if not user_feedback:
        # No feedback to process
        return state
    
    startup_name = state["startup_name"]
    fit_reasoning = state.get("fit_reasoning", "Keine Begründung verfügbar")
    obsidian_paths = state["obsidian_paths"]
    
    # Load current user profile from Obsidian
    profile_path = obsidian_paths.get("profile", "./obsidian_vault/startup-screening/profile.md")
    try:
        current_profile = read_from_obsidian(profile_path)
    except FileNotFoundError:
        current_profile = _get_default_user_profile()
    
    # Format context for LLM
    context = _format_context_for_llm(current_profile, fit_reasoning, user_feedback, startup_name)
    
    # Initialize LLM
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        # Fallback: append feedback note to profile
        updated_profile = current_profile + f"\n\n---\n⚠️ Feedback erhalten (API-Key fehlt): {user_feedback}\n"
    else:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Create messages
        system_message = SystemMessage(content=PROFILE_UPDATER_PROMPT)
        human_message = HumanMessage(content=context)
        
        # Call LLM
        response = llm.invoke([system_message, human_message])
        updated_profile = response.content
    
    # Write updated profile to Obsidian
    save_to_obsidian(profile_path, updated_profile)
    
    # Append to feedback log
    feedback_log_path = obsidian_paths.get("feedback_log", "./obsidian_vault/startup-screening/feedback-log.md")
    try:
        append_feedback(
            feedback_log_path=feedback_log_path,
            startup_name=startup_name,
            original_reasoning=fit_reasoning,
            user_feedback=user_feedback
        )
    except Exception as e:
        # Log error but don't fail the whole process
        print(f"Warning: Could not append to feedback log: {e}")
    
    return state


def _format_context_for_llm(
    current_profile: str,
    fit_reasoning: str,
    user_feedback: str,
    startup_name: str
) -> str:
    """Formatiert den Kontext für den LLM-Call."""
    context = f"""Startup: {startup_name}

## Aktuelles User Profil

{current_profile}

## Matchmaker Begründung (Original-Analyse)

{fit_reasoning}

## User Feedback (Neue Erkenntnisse)

{user_feedback}

Bitte aktualisiere das User Profil basierend auf diesem Feedback. Das Profil soll präziser und spezifischer werden."""
    
    return context


def _get_default_user_profile() -> str:
    """Returns default user profile if none exists."""
    return """# Mein Profil

## Hintergrund
- Abiturient (kein Uni-Abschluss)
- Suche Praktikum als Founder's Associate / Product Builder
- Hochmotiviert und lernbegierig

## Skills
- Schnell im Lernen neuer Technologien
- Praktische Erfahrung bevorzugt über theoretisches Wissen
- Interesse an Product Development und Business Strategy

## Präferenzen
- Startup-Größe: < 20 Mitarbeiter (direkter Founder-Kontakt wichtig)
- Arbeitsstil: Remote-first oder hybrid
- Kultur: Transparent, flache Hierarchien
- Branche: Tech / SaaS bevorzugt
- Standort: DACH-Region (Deutschland, Österreich, Schweiz)

## Was mir wichtig ist
- Direkte Mentorschaft durch Founder
- Echter Impact (keine Kaffeekoch-Jobs)
- Lernmöglichkeiten > Bezahlung
- Authentische Unternehmenskultur

## Deal-Breaker
- "Work hard, play hard" Mentalität
- Reine Präsenzkultur ohne Flexibilität
- Unklare Rollenbeschreibung
- Gründer ohne Previous Experience"""
