"""Profiler Agent Node - Analysiert Kultur-Profil aus Rohdaten."""

from typing import Dict, Any
import json
from state import AgentState
from tools.obsidian_writer import save_to_obsidian
from config.prompts import PROFILER_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


def profiler_node(state: AgentState) -> AgentState:
    """
    Analysiert die Rohdaten und extrahiert das Kultur-Profil.
    
    1. Lade system_prompt aus config/prompts.py (PROFILER_PROMPT)
    2. Formatiere raw_data als Kontext
    3. Mache LLM-Call mit LangChain (ChatOpenAI)
    4. Parse die Antwort in ein strukturiertes Dict
    5. Speichere in state['culture_profile']
    6. Schreibe culture-profile.md in Obsidian
    
    Returns: Updated state
    """
    raw_data = state["raw_data"]
    obsidian_paths = state["obsidian_paths"]
    
    # Format raw data as context string
    context = _format_raw_data_for_llm(raw_data)
    
    # Initialize LLM
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        # Fallback: create a mock profile if no API key
        culture_profile = _create_mock_profile(raw_data)
    else:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Create messages
        system_message = SystemMessage(content=PROFILER_PROMPT)
        human_message = HumanMessage(
            content=f"Analysiere dieses Startup basierend auf den gesammelten Daten:\n\n{context}"
        )
        
        # Call LLM
        response = llm.invoke([system_message, human_message])
        response_content = response.content
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            culture_profile = _extract_json_from_response(response_content)
        except Exception as e:
            # Fallback if parsing fails
            culture_profile = _create_fallback_profile(response_content, raw_data)
    
    # Update state
    state["culture_profile"] = culture_profile
    
    # Write culture-profile.md to Obsidian
    profile_content = _format_culture_profile_markdown(culture_profile, state["startup_name"])
    save_to_obsidian(obsidian_paths["culture_profile"], profile_content)
    
    return state


def _format_raw_data_for_llm(raw_data: Dict) -> str:
    """Formatiert Rohdaten für den LLM-Kontext."""
    context_parts = []
    
    # Web data
    web_data = raw_data.get("web_data", {})
    if web_data and "error" not in web_data:
        context_parts.append("## Web-Daten")
        for key, value in web_data.items():
            context_parts.append(f"### {key}\n{value}")
    
    # Podcasts
    podcasts = raw_data.get("podcasts", [])
    if podcasts:
        context_parts.append("## Gefundene Podcasts")
        for podcast in podcasts:
            context_parts.append(f"- {podcast.get('title', 'Unknown')}: {podcast.get('url', 'N/A')}")
    
    # Transcripts
    transcripts = raw_data.get("transcripts", [])
    if transcripts:
        context_parts.append("## Transkripte")
        for t in transcripts:
            if "transcript" in t:
                podcast_title = t.get("podcast_info", {}).get("title", "Unknown")
                context_parts.append(f"### {podcast_title}\n{t['transcript'][:2000]}")  # Limit length
    
    return "\n\n".join(context_parts)


def _extract_json_from_response(response_content: str) -> Dict[str, Any]:
    """Extrahiert JSON aus der LLM-Antwort."""
    # Try to find JSON block in response
    import re
    json_match = re.search(r'\{[\s\S]*\}', response_content)
    if json_match:
        json_str = json_match.group()
        return json.loads(json_str)
    else:
        # Try parsing the whole response as JSON
        return json.loads(response_content)


def _create_fallback_profile(response_content: str, raw_data: Dict) -> Dict[str, Any]:
    """Erstellt ein Fallback-Profil wenn JSON-Parsing fehlschlägt."""
    startup_name = raw_data.get("startup_name", "Unknown")
    return {
        "core_philosophy": response_content[:500] if response_content else "Nicht verfügbar",
        "communication_style": "Unbekannt",
        "tech_stack": "Unbekannt",
        "red_flags": [],
        "green_flags": ["Daten wurden erfolgreich gesammelt"],
        "media_presence": {
            "podcasts": raw_data.get("podcasts", []),
            "interviews": []
        }
    }


def _create_mock_profile(raw_data: Dict) -> Dict[str, Any]:
    """Erstellt ein Mock-Profil wenn keine API-Key vorhanden ist."""
    startup_name = raw_data.get("startup_name", "Unknown")
    return {
        "core_philosophy": f"Mock-Analyse für {startup_name} (OPENAI_API_KEY nicht gesetzt)",
        "communication_style": "Unbekannt - bitte API-Key konfigurieren",
        "tech_stack": "Unbekannt",
        "red_flags": ["API-Key fehlt für vollständige Analyse"],
        "green_flags": [],
        "media_presence": {
            "podcasts": raw_data.get("podcasts", []),
            "interviews": []
        }
    }


def _format_culture_profile_markdown(profile: Dict, startup_name: str) -> str:
    """Formatiert das Kultur-Profil als Markdown für Obsidian."""
    md = f"# Kultur-Profil: {startup_name}\n\n"
    md += "---\ntags: [startup, culture-profile]\n---\n\n"
    
    md += f"## Core Philosophy\n\n{profile.get('core_philosophy', 'N/A')}\n\n"
    
    md += f"## Kommunikationsstil\n\n{profile.get('communication_style', 'N/A')}\n\n"
    
    md += f"## Tech Stack\n\n{profile.get('tech_stack', 'N/A')}\n\n"
    
    md += "## Red Flags 🚩\n\n"
    red_flags = profile.get('red_flags', [])
    if red_flags:
        for flag in red_flags:
            md += f"- ⚠️ {flag}\n"
    else:
        md += "*Keine Red Flags identifiziert*\n"
    md += "\n"
    
    md += "## Green Flags ✅\n\n"
    green_flags = profile.get('green_flags', [])
    if green_flags:
        for flag in green_flags:
            md += f"- ✅ {flag}\n"
    else:
        md += "*Keine Green Flags identifiziert*\n"
    md += "\n"
    
    md += "## Media Presence\n\n"
    media = profile.get('media_presence', {})
    
    md += "### Podcasts\n\n"
    podcasts = media.get('podcasts', [])
    if podcasts:
        for podcast in podcasts:
            title = podcast.get('title', 'Unknown')
            url = podcast.get('url', 'N/A')
            date = podcast.get('date', '')
            md += f"- [{title}]({url})"
            if date:
                md += f" ({date})"
            md += "\n"
    else:
        md += "*Keine Podcasts gefunden*\n"
    md += "\n"
    
    md += "### Interviews\n\n"
    interviews = media.get('interviews', [])
    if interviews:
        for interview in interviews:
            title = interview.get('title', 'Unknown')
            url = interview.get('url', 'N/A')
            source = interview.get('source', '')
            md += f"- [{title}]({url})"
            if source:
                md += f" via {source}"
            md += "\n"
    else:
        md += "*Keine Interviews gefunden*\n"
    md += "\n"
    
    md += "---\n*Automatisch generiert vom Profiler Agent*\n"
    
    return md
