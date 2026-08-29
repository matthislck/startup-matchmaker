"""Scout Agent Node - Sammelt Daten über Startups mit robustem Scraping-Stack."""

import os
import logging
from datetime import datetime
from typing import Dict, List

from state import AgentState
from tools.scraping_stack import scrape_startup_comprehensive, format_for_llm
from tools.obsidian_writer import ensure_obsidian_structure, save_to_obsidian
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def scout_node(state: AgentState) -> AgentState:
    """
    Sammelt alle verfügbaren Daten über das Startup.
    
    1. Nutze scraping_stack.scrape_startup_comprehensive() für alle Quellen
    2. Speichere Rohdaten in state['raw_data']
    3. Speichere Pfade in state['obsidian_paths']
    4. Schreibe strukturierte raw-data.md in Obsidian
    
    Returns: Updated state
    """
    startup_name = state["startup_name"]
    logger.info(f"Scout node started for: {startup_name}")
    
    # Hole Vault Path aus Env
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")
    
    # Erstelle Obsidian-Struktur
    obsidian_paths = ensure_obsidian_structure(vault_path, startup_name)
    
    # Hole optionale Founder-Namen aus State (User-Override)
    founder_names = state.get("founder_names", [])
    
    try:
        # Führe umfassendes Scraping durch
        raw_data = scrape_startup_comprehensive(
            startup_name=startup_name,
            founder_names=founder_names if founder_names else None,
            website_url=None  # Wird automatisch erraten
        )
        
        # Speichere im State
        state["raw_data"] = raw_data
        state["obsidian_paths"] = obsidian_paths
        
        # Generiere Markdown für raw-data.md
        md_content = _format_raw_data_markdown(raw_data)
        
        # Speichere in Obsidian
        save_to_obsidian(obsidian_paths["raw_data"], md_content)
        logger.info(f"Raw data saved to {obsidian_paths['raw_data']}")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        state["raw_data"] = {"error": str(e), "startup_name": startup_name}
        
        # Speichere Fehler in Obsidian
        error_md = f"""# Fehler beim Scraping: {startup_name}

**Zeitpunkt:** {datetime.now().isoformat()}

**Fehlermeldung:**
{str(e)}

## Nächste Schritte
1. Prüfe ob API Keys in .env gesetzt sind (TAVILY_API_KEY, OPENAI_API_KEY)
2. Prüfe Internetverbindung
3. Versuche es erneut mit: `python main.py --startup "{startup_name}"`
"""
        save_to_obsidian(obsidian_paths["raw_data"], error_md)
    
    return state


def _format_raw_data_markdown(raw_data: Dict) -> str:
    """
    Formatiert Rohdaten als strukturiertes Markdown für Obsidian.
    
    Ziel: User soll auf einen Blick sehen:
    1. Datenqualität und Quellenanzahl
    2. Website-Infos
    3. News & Presse
    4. Kununu-Bewertungen (DACH-spezifisch)
    5. YouTube Interviews mit Transkripten
    6. GitHub Tech-Stack
    """
    startup_name = raw_data.get('startup_name', 'Unknown')
    scraped_at = raw_data.get('scraped_at', datetime.now().isoformat())
    data_quality = raw_data.get('data_quality', 'unknown').upper()
    sources_count = raw_data.get('sources_count', 0)
    
    md = f"# Raw Data: {startup_name}\n\n"
    md += f"**Erstellt am:** {scraped_at}\n"
    md += f"**Datenqualität:** {data_quality} ({sources_count} Quellen)\n\n"
    md += "---\n\n"
    
    # ========================================
    # WEBSITE CONTENT
    # ========================================
    md += "## 🌐 Website Inhalte\n\n"
    website = raw_data.get('website', {})
    
    if website:
        if website.get('homepage'):
            md += f"### Homepage\n{website['homepage'][:1500]}...\n\n"
        
        if website.get('about'):
            md += f"### About Us\n{website['about'][:1000]}...\n\n"
        
        if website.get('team'):
            md += f"### Team\n{website['team'][:1000]}...\n\n"
        
        if website.get('impressum'):
            md += f"### Impressum (DACH)\n{website['impressum'][:800]}...\n\n"
    else:
        md += "*Keine Website-Inhalte gefunden.*\n\n"
    
    # ========================================
    # NEWS & PRESSE
    # ========================================
    md += "## 📰 News & Presse\n\n"
    news = raw_data.get('news', [])
    
    if news:
        for i, article in enumerate(news[:10], 1):
            md += f"{i}. **{article.get('title', 'Unknown')}**\n"
            md += f"   - Quelle: {article.get('url', 'N/A')}\n"
            md += f"   - Inhalt: {article.get('content', '')[:300]}...\n\n"
    else:
        md += "*Keine News-Artikel gefunden.*\n\n"
    
    # ========================================
    # KUNUNU (DACH-Kultur-Signale)
    # ========================================
    md += "## ⭐ Kununu Bewertungen (DACH)\n\n"
    kununu = raw_data.get('kununu', [])
    
    if kununu:
        for i, review in enumerate(kununu[:5], 1):
            md += f"{i}. **{review.get('title', 'Unknown')}**\n"
            md += f"   - URL: {review.get('url', 'N/A')}\n"
            md += f"   - Inhalt: {review.get('content', '')[:300]}...\n\n"
    else:
        md += "*Keine Kununu-Bewertungen gefunden.*\n\n"
    
    # ========================================
    # CRUNCHBASE & PRODUCT HUNT
    # ========================================
    crunchbase = raw_data.get('crunchbase', [])
    producthunt = raw_data.get('producthunt', [])
    
    if crunchbase or producthunt:
        md += "## 💰 Funding & Launches\n\n"
        
        if crunchbase:
            md += "### Crunchbase\n"
            for cb in crunchbase[:3]:
                md += f"- {cb.get('title', 'Unknown')}: {cb.get('content', '')[:200]}...\n\n"
        
        if producthunt:
            md += "\n### Product Hunt\n"
            for ph in producthunt[:3]:
                md += f"- {ph.get('title', 'Unknown')}: {ph.get('content', '')[:200]}...\n\n"
        
        md += "\n"
    
    # ========================================
    # LINKEDIN
    # ========================================
    md += "## 💼 LinkedIn\n\n"
    linkedin = raw_data.get('social_media', {}).get('linkedin_company', [])
    
    if linkedin:
        for li in linkedin[:5]:
            md += f"- **{li.get('title', 'Unknown')}**\n"
            md += f"  {li.get('content', '')[:200]}...\n\n"
    else:
        md += "*Keine LinkedIn-Infos gefunden.*\n\n"
    
    # ========================================
    # YOUTUBE INTERVIEWS MIT TRANSKRIPTEN
    # ========================================
    md += "## 📺 YouTube Interviews & Podcasts\n\n"
    
    youtube_found = False
    social_media = raw_data.get('social_media', {})
    
    for key, value in social_media.items():
        if key.startswith('founder_') and isinstance(value, dict):
            youtube = value.get('youtube', [])
            if youtube:
                youtube_found = True
                founder_name = key.replace('founder_', '').replace('_', ' ').title()
                md += f"### {founder_name}\n\n"
                
                for video in youtube[:3]:
                    md += f"#### {video.get('title', 'Unknown')}\n"
                    md += f"**URL:** {video.get('url', 'N/A')}\n"
                    
                    transcript = video.get('transcript', '')
                    if transcript:
                        md += f"**Transkript Länge:** {len(transcript)} Zeichen\n"
                        md += f"**Auszug:** {transcript[:1000]}...\n\n"
                    else:
                        md += "*Kein Transkript verfügbar*\n\n"
    
    if not youtube_found:
        md += "*Keine YouTube-Interviews gefunden.*\n\n"
    
    # ========================================
    # GITHUB TECH-STACK
    # ========================================
    md += "## 📦 GitHub & Tech-Stack\n\n"
    github = raw_data.get('github', {})
    
    if github and not github.get('error'):
        md += f"**Organization:** {github.get('org_name', 'N/A')}\n"
        md += f"**Öffentliche Repos:** {github.get('public_repos', 0)}\n"
        md += f"**Tech-Stack:** {', '.join(github.get('tech_stack', [])) or 'N/A'}\n\n"
        
        repos = github.get('repos', [])
        if repos:
            md += "### Top Repositories\n\n"
            for repo in repos[:5]:
                stars = repo.get('stars', 0)
                lang = repo.get('language', 'Unknown')
                desc = repo.get('description', '')[:100]
                md += f"- **{repo.get('name', 'Unknown')}** | ⭐ {stars} | {lang}\n"
                md += f"  {desc}...\n"
    elif github.get('error'):
        md += f"*GitHub-Analyse fehlgeschlagen: {github.get('error')}*\n\n"
    else:
        md += "*Keine GitHub-Organisation gefunden.*\n\n"
    
    # ========================================
    # REDDIT DISCUSSIONS
    # ========================================
    md += "## 📖 Reddit Diskussionen\n\n"
    reddit = raw_data.get('reddit', [])
    
    if reddit:
        for discussion in reddit[:5]:
            md += f"- **{discussion.get('title', 'Unknown')}**\n"
            md += f"  {discussion.get('content', '')[:200]}...\n\n"
    else:
        md += "*Keine Reddit-Diskussionen gefunden.*\n\n"
    
    # ========================================
    # FOOTER
    # ========================================
    md += "---\n"
    md += "*Automatisch generiert vom Scout Agent*\n"
    md += f"*Datenqualität: {data_quality} bei {sources_count} Quellen*\n"
    
    return md
