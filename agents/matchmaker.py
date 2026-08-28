"""Matchmaker Agent Node - Vergleicht Startup-Profil mit User-Präferenzen."""

from typing import Dict, Any
import json
import re
from state import AgentState
from tools.obsidian_writer import read_from_obsidian, save_to_obsidian
from config.prompts import MATCHMAKER_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


def matchmaker_node(state: AgentState) -> AgentState:
    """
    Vergleicht das Startup-Profil mit den User-Präferenzen.
    
    1. Lade profile.md aus Obsidian (User-Präferenzen)
    2. Lade MATCHMAKER_PROMPT aus config/prompts.py
    3. Mache LLM-Call mit:
       - User Profile als Kontext
       - Culture Profile als Kontext
    4. Parse die Antwort:
       {
         "fit_score": int,
         "fit_reasoning": str,
         "recommendation": str
       }
    5. Speichere in state
    6. Schreibe match-analysis.md in Obsidian
    
    Returns: Updated state
    """
    culture_profile = state["culture_profile"]
    obsidian_paths = state["obsidian_paths"]
    startup_name = state["startup_name"]
    
    # Load user profile from Obsidian
    profile_path = obsidian_paths.get("profile", "./obsidian_vault/startup-screening/profile.md")
    try:
        user_profile = read_from_obsidian(profile_path)
    except FileNotFoundError:
        user_profile = _get_default_user_profile()
    
    # Format context for LLM
    context = _format_context_for_llm(user_profile, culture_profile, startup_name)
    
    # Initialize LLM
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        # Fallback: create a mock match analysis
        fit_score = 50
        fit_reasoning = "Mock-Analyse: OPENAI_API_KEY nicht gesetzt. Bitte konfigurieren für echte Bewertung."
        recommendation = "Bedingt bewerben"
    else:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Create messages
        system_message = SystemMessage(content=MATCHMAKER_PROMPT)
        human_message = HumanMessage(content=context)
        
        # Call LLM
        response = llm.invoke([system_message, human_message])
        response_content = response.content
        
        # Parse JSON response
        try:
            result = _extract_json_from_response(response_content)
            fit_score = result.get("fit_score", 50)
            fit_reasoning = result.get("fit_reasoning", "Keine Begründung verfügbar")
            recommendation = result.get("recommendation", "Unklar")
        except Exception as e:
            # Fallback if parsing fails
            fit_score = 50
            fit_reasoning = f"Fehler beim Parsen der LLM-Antwort: {str(e)}\n\nRaw Response: {response_content[:500]}"
            recommendation = "Bedingt bewerben"
    
    # Update state
    state["fit_score"] = fit_score
    state["fit_reasoning"] = fit_reasoning
    
    # Write match-analysis.md to Obsidian
    analysis_content = _format_match_analysis_markdown(
        startup_name, culture_profile, fit_score, fit_reasoning, recommendation
    )
    save_to_obsidian(obsidian_paths["match_analysis"], analysis_content)
    
    return state


def _format_context_for_llm(user_profile: str, culture_profile: Dict, startup_name: str) -> str:
    """Formatiert den Kontext für den LLM-Call."""
    context = f"""Startup: {startup_name}

## User Profil (Deine Präferenzen)

{user_profile}

## Startup Kultur-Profil

**Core Philosophy**: {culture_profile.get('core_philosophy', 'N/A')}

**Kommunikationsstil**: {culture_profile.get('communication_style', 'N/A')}

**Tech Stack**: {culture_profile.get('tech_stack', 'N/A')}

**Red Flags**: {', '.join(culture_profile.get('red_flags', [])) or 'Keine'}

**Green Flags**: {', '.join(culture_profile.get('green_flags', [])) or 'Keine'}

Bitte bewerte nun den Fit zwischen dem User und diesem Startup."""
    
    return context


def _extract_json_from_response(response_content: str) -> Dict[str, Any]:
    """Extrahiert JSON aus der LLM-Antwort."""
    # Try to find JSON block in response
    json_match = re.search(r'\{[\s\S]*\}', response_content)
    if json_match:
        json_str = json_match.group()
        return json.loads(json_str)
    else:
        # Try parsing the whole response as JSON
        return json.loads(response_content)


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


def _format_match_analysis_markdown(
    startup_name: str,
    culture_profile: Dict,
    fit_score: int,
    fit_reasoning: str,
    recommendation: str
) -> str:
    """Formatiert die Match-Analyse als Markdown für Obsidian."""
    # Determine emoji based on score
    if fit_score >= 80:
        emoji = "🎯"
    elif fit_score >= 70:
        emoji = "✅"
    elif fit_score >= 50:
        emoji = "⚠️"
    else:
        emoji = "❌"
    
    md = f"# Match-Analyse: {startup_name}\n\n"
    md += "---\ntags: [startup, match-analysis]\n---\n\n"
    
    md += f"## Fit Score: {fit_score}/100 {emoji}\n\n"
    
    md += f"## Empfehlung: {recommendation}\n\n"
    
    md += "## Detaillierte Begründung\n\n"
    md += fit_reasoning + "\n\n"
    
    md += "## Startup Kultur-Zusammenfassung\n\n"
    md += f"**Philosophie**: {culture_profile.get('core_philosophy', 'N/A')[:200]}...\n\n"
    
    red_flags = culture_profile.get('red_flags', [])
    green_flags = culture_profile.get('green_flags', [])
    
    if red_flags:
        md += "### Red Flags\n"
        for flag in red_flags:
            md += f"- ⚠️ {flag}\n"
        md += "\n"
    
    if green_flags:
        md += "### Green Flags\n"
        for flag in green_flags:
            md += f"- ✅ {flag}\n"
        md += "\n"
    
    md += "---\n"
    md += "*Automatisch generiert vom Matchmaker Agent*\n\n"
    md += "## Dein Feedback\n\n"
    md += "> Kommentiere hier deine Gedanken zur Analyse. Das System wird daraus lernen.\n>\n"
    md += "> **Beispiel**: \"Remote-First ist mir wichtiger als du denkst. Bitte gewichte das stärker.\"\n\n"
    
    return md
