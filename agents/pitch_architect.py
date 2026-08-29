"""Pitch Architect Agent Node - Generiert Door-Opener Projektvorschlag."""

from typing import Dict, Any
import json
import re
from state import AgentState
from tools.obsidian_writer import read_from_obsidian, save_to_obsidian
from config.prompts import PITCH_ARCHITECT_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


def pitch_architect_node(state: AgentState) -> AgentState:
    """
    Generiert einen maßgeschneiderten Projektvorschlag.
    
    1. Lade PITCH_ARCHITECT_PROMPT aus config/prompts.py
    2. Mache LLM-Call mit:
       - Culture Profile
       - Fit Reasoning
       - User Skills (aus profile.md)
    3. Parse die Antwort:
       {
         "project_title": str,
         "problem_statement": str,
         "proposed_solution": List[str],
         "expected_impact": str,
         "cold_outreach_message": str
       }
    4. Speichere in state['pitch_draft']
    5. Schreibe pitch-proposal.md in Obsidian
    
    Returns: Updated state
    """
    culture_profile = state["culture_profile"]
    fit_reasoning = state["fit_reasoning"]
    startup_name = state["startup_name"]
    obsidian_paths = state["obsidian_paths"]
    
    # Load user profile from Obsidian
    profile_path = obsidian_paths.get("profile", "./obsidian_vault/startup-screening/profile.md")
    try:
        user_profile = read_from_obsidian(profile_path)
    except FileNotFoundError:
        user_profile = _get_default_user_profile()
    
    # Format context for LLM
    context = _format_context_for_llm(user_profile, culture_profile, fit_reasoning, startup_name)
    
    # Initialize LLM
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        # Fallback: create a mock pitch
        pitch_data = _create_mock_pitch(startup_name, culture_profile)
    else:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        
        # Create messages
        system_message = SystemMessage(content=PITCH_ARCHITECT_PROMPT)
        human_message = HumanMessage(content=context)
        
        # Call LLM
        response = llm.invoke([system_message, human_message])
        response_content = response.content
        
        # Parse JSON response
        try:
            pitch_data = _extract_json_from_response(response_content)
        except Exception as e:
            # Fallback if parsing fails
            pitch_data = _create_fallback_pitch(response_content, startup_name)
    
    # Update state
    state["pitch_draft"] = json.dumps(pitch_data, ensure_ascii=False)
    
    # Write pitch-proposal.md to Obsidian
    proposal_content = _format_pitch_proposal_markdown(pitch_data, startup_name)
    save_to_obsidian(obsidian_paths["pitch_proposal"], proposal_content)
    
    return state


def _format_context_for_llm(
    user_profile: str, 
    culture_profile: Dict, 
    fit_reasoning: str, 
    startup_name: str
) -> str:
    """Formatiert den Kontext für den LLM-Call."""
    context = f"""Startup: {startup_name}

## User Profil (Skills & Präferenzen)

{user_profile}

## Startup Kultur-Profil

**Core Philosophy**: {culture_profile.get('core_philosophy', 'N/A')}

**Kommunikationsstil**: {culture_profile.get('communication_style', 'N/A')}

**Tech Stack**: {culture_profile.get('tech_stack', 'N/A')}

**Green Flags**: {', '.join(culture_profile.get('green_flags', [])) or 'Keine'}

**Red Flags**: {', '.join(culture_profile.get('red_flags', [])) or 'Keine'}

## Matchmaker Begründung

{fit_reasoning}

Basierend auf diesen Informationen, erstelle einen maßgeschneiderten Door-Opener Projektvorschlag."""
    
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


def _create_mock_pitch(startup_name: str, culture_profile: Dict) -> Dict[str, Any]:
    """Erstellt einen Mock-Pitch wenn keine API-Key vorhanden ist."""
    return {
        "project_title": f"Mock Project für {startup_name}",
        "problem_statement": "API-Key fehlt - bitte konfigurieren für echten Vorschlag",
        "proposed_solution": ["API-Key setzen", "System neu ausführen"],
        "expected_impact": "Ein echter Pitch würde konkrete Probleme adressieren",
        "cold_outreach_message": f"Hallo Gründer von {startup_name},\n\nIch bin beeindruckt von eurer Arbeit..."
    }


def _create_fallback_pitch(response_content: str, startup_name: str) -> Dict[str, Any]:
    """Erstellt einen Fallback-Pitch wenn JSON-Parsing fehlschlägt."""
    return {
        "project_title": f"Projektvorschlag für {startup_name}",
        "problem_statement": response_content[:300] if response_content else "N/A",
        "proposed_solution": ["Siehe Raw Response für Details"],
        "expected_impact": "Unbekannt",
        "cold_outreach_message": "Bitte API konfigurieren für besseren Pitch"
    }


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
- Standort: DACH-Region (Deutschland, Österreich, Schweiz)"""


def _format_pitch_proposal_markdown(pitch_data: Dict, startup_name: str) -> str:
    """Formatiert den Pitch-Vorschlag als Markdown für Obsidian."""
    md = f"# Pitch Proposal: {startup_name}\n\n"
    md += "---\ntags: [startup, pitch-proposal, door-opener]\n---\n\n"
    
    md += f"## 🎯 {pitch_data.get('project_title', 'Projektvorschlag')}\n\n"
    
    md += "## Problem Statement\n\n"
    md += pitch_data.get('problem_statement', 'N/A') + "\n\n"
    
    md += "## Proposed Solution\n\n"
    proposed_solution = pitch_data.get('proposed_solution', [])
    if proposed_solution:
        for i, step in enumerate(proposed_solution, 1):
            md += f"{i}. {step}\n"
    else:
        md += "*Keine Lösungsschritte verfügbar*\n"
    md += "\n"
    
    md += "## Expected Impact\n\n"
    md += pitch_data.get('expected_impact', 'N/A') + "\n\n"
    
    md += "## 📧 Cold Outreach Message\n\n"
    md += "```markdown\n"
    md += pitch_data.get('cold_outreach_message', 'N/A') + "\n"
    md += "```\n\n"
    
    md += "---\n"
    md += "*Automatisch generiert vom Pitch Architect Agent*\n\n"
    md += "## Nächste Schritte\n\n"
    md += "1. ✅ Nachricht personalisieren (echte Namen einfügen)\n"
    md += "2. ✅ Startup-spezifische Details recherchieren\n"
    md += "3. ✅ Über LinkedIn oder Email senden\n"
    md += "4. ⏳ Nach 3-5 Tagen nachfassen wenn keine Antwort\n\n"
    
    md += "## Tipps für die Nachricht\n\n"
    md += "- **Betreffzeile**: Kurz und prägnant (max. 50 Zeichen)\n"
    md += "- **Länge**: Unter 200 Wörtern bleiben\n"
    md += "- **CTA**: Klare, einfache Handlungsaufforderung\n"
    md += "- **Timing**: Dienstag-Donnerstag morgens sind optimal\n"
    
    return md
