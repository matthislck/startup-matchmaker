"""Scout Agent Node - Sammelt Daten über Startups."""

from typing import Dict
from state import AgentState
from tools.web_scraper import scrape_startup_data
from tools.podcast_transcriber import find_podcast_episodes, transcribe_podcast
from tools.obsidian_writer import ensure_obsidian_structure, save_to_obsidian
import os
from dotenv import load_dotenv

load_dotenv()


def scout_node(state: AgentState) -> AgentState:
    """
    Sammelt alle verfügbaren Daten über das Startup.
    
    1. Nutze web_scraper.scrape_startup_data()
    2. Nutze podcast_transcriber.find_podcast_episodes()
    3. Wenn Podcasts gefunden: transcribe_podcast() für die ersten 2
    4. Speichere alle Rohdaten in state['raw_data']
    5. Speichere Pfade in state['obsidian_paths']
    6. Schreibe raw-data.md in Obsidian
    
    Returns: Updated state
    """
    startup_name = state["startup_name"]
    
    # Ensure obsidian structure exists
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")
    obsidian_paths = ensure_obsidian_structure(vault_path, startup_name)
    
    # Scrape web data
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")
    if tavily_api_key:
        raw_web_data = scrape_startup_data(startup_name, tavily_api_key)
    else:
        raw_web_data = {
            "error": "TAVILY_API_KEY not set",
            "startup_name": startup_name,
            "note": "Web scraping skipped due to missing API key"
        }
    
    # Find podcast episodes
    podcasts = find_podcast_episodes(startup_name)
    
    # Transcribe first 2 podcasts if available
    transcripts = []
    for podcast in podcasts[:2]:
        try:
            transcript = transcribe_podcast(podcast["url"])
            transcripts.append({
                "podcast_info": podcast,
                "transcript": transcript
            })
        except Exception as e:
            transcripts.append({
                "podcast_info": podcast,
                "transcript_error": str(e)
            })
    
    # Compile all raw data
    raw_data = {
        "web_data": raw_web_data,
        "podcasts": podcasts,
        "transcripts": transcripts,
        "startup_name": startup_name
    }
    
    # Update state
    state["raw_data"] = raw_data
    state["obsidian_paths"] = obsidian_paths
    
    # Write raw-data.md to Obsidian
    raw_data_content = _format_raw_data_markdown(raw_data)
    save_to_obsidian(obsidian_paths["raw_data"], raw_data_content)
    
    return state


def _format_raw_data_markdown(raw_data: Dict) -> str:
    """Formatiert Rohdaten als Markdown für Obsidian."""
    startup_name = raw_data.get("startup_name", "Unknown")
    
    md = f"# Raw Data: {startup_name}\n\n"
    md += "---\ntags: [startup, raw-data]\n---\n\n"
    
    # Web Data Section
    md += "## Web-Daten\n\n"
    web_data = raw_data.get("web_data", {})
    if "error" in web_data:
        md += f"⚠️ **Fehler**: {web_data['error']}\n\n"
    else:
        for key, value in web_data.items():
            md += f"### {key}\n{value}\n\n"
    
    # Podcasts Section
    md += "## Gefundene Podcasts\n\n"
    podcasts = raw_data.get("podcasts", [])
    if podcasts:
        for i, podcast in enumerate(podcasts, 1):
            md += f"{i}. **{podcast.get('title', 'Unknown')}**\n"
            md += f"   - URL: {podcast.get('url', 'N/A')}\n"
            md += f"   - Dauer: {podcast.get('duration', 'N/A')}\n\n"
    else:
        md += "*Keine Podcast-Episoden gefunden.*\n\n"
    
    # Transcripts Section
    md += "## Transkripte\n\n"
    transcripts = raw_data.get("transcripts", [])
    if transcripts:
        for i, t in enumerate(transcripts, 1):
            if "transcript" in t:
                md += f"### Transkript {i}\n"
                md += f"**Quelle**: {t['podcast_info'].get('title', 'Unknown')}\n\n"
                md += f"{t['transcript']}\n\n"
            elif "transcript_error" in t:
                md += f"### Transkript {i} (Fehler)\n"
                md += f"**Quelle**: {t['podcast_info'].get('title', 'Unknown')}\n"
                md += f"⚠️ {t['transcript_error']}\n\n"
    else:
        md += "*Keine Transkripte verfügbar.*\n\n"
    
    md += "---\n*Automatisch generiert vom Scout Agent*\n"
    
    return md
