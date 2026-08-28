import subprocess
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def run_agent_reach_command(command: str, timeout: int = 60) -> str:
    """
    Führt einen agent-reach CLI-Befehl aus.
    
    Args:
        command: Der auszuführende Befehl
        timeout: Timeout in Sekunden (default: 60)
        
    Returns:
        Output des Befehls als String, oder leerer String bei Fehler
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            logger.warning(f"Command failed: {command}\nError: {result.stderr}")
            return ""
        
        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out after {timeout}s: {command}")
        return ""
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return ""


def scrape_website(url: str) -> str:
    """Scrapet eine beliebige Webseite mit Jina Reader."""
    return run_agent_reach_command(f"curl -s https://r.jina.ai/{url}")


def scrape_linkedin_company(company_name: str) -> str:
    """Scrapet LinkedIn-Company-Page."""
    return run_agent_reach_command(f"agent-reach linkedin company '{company_name}'")


def scrape_linkedin_founder(linkedin_handle: str) -> List[Dict]:
    """
    Scrapet LinkedIn-Posts eines Gründers.
    
    Returns:
        Liste von Posts mit content, date, etc.
    """
    output = run_agent_reach_command(f"agent-reach linkedin user '{linkedin_handle}'")
    
    # Parse JSON output (falls agent-reach JSON zurückgibt)
    try:
        if output.startswith("{") or output.startswith("["):
            return json.loads(output)
    except:
        pass
    
    # Fallback: Return raw text als einzelnes "Post"
    return [{"content": output, "date": "unknown"}] if output else []


def scrape_twitter_founder(twitter_handle: str) -> List[Dict]:
    """Scrapet Twitter-Profile und Tweets."""
    output = run_agent_reach_command(f"agent-reach twitter user '{twitter_handle}'")
    
    try:
        if output.startswith("{") or output.startswith("["):
            return json.loads(output)
    except:
        pass
    
    return [{"text": output, "date": "unknown"}] if output else []


def scrape_youtube_search(query: str) -> List[Dict]:
    """
    Sucht nach YouTube-Videos (Interviews, Podcasts).
    
    Returns:
        Liste von Videos mit title, url, duration
    """
    output = run_agent_reach_command(f"agent-reach youtube search '{query}'")
    
    try:
        if output.startswith("["):
            return json.loads(output)
    except:
        pass
    
    # Fallback: Parse manuell (falls kein JSON)
    videos = []
    for line in output.split("\n"):
        if "youtube.com/watch" in line or "youtu.be" in line:
            videos.append({
                "title": line.split(" - ")[0] if " - " in line else "Unknown",
                "url": line.strip(),
                "duration": "unknown"
            })
    
    return videos[:5]  # Max 5 Videos


def scrape_youtube_transcript(video_url: str) -> str:
    """Extrahiert Transkript von YouTube-Video."""
    return run_agent_reach_command(f"agent-reach youtube transcript '{video_url}'")


def scrape_reddit_discussions(startup_name: str) -> List[Dict]:
    """Scrapet Reddit-Diskussionen über das Startup."""
    output = run_agent_reach_command(f"agent-reach reddit search '{startup_name}'")
    
    try:
        if output.startswith("["):
            return json.loads(output)
    except:
        pass
    
    return []


def scrape_github_org(org_name: str) -> Dict:
    """Scrapet GitHub-Organization."""
    output = run_agent_reach_command(f"agent-reach github org '{org_name}'")
    
    try:
        if output.startswith("{"):
            return json.loads(output)
    except:
        pass
    
    return {"raw_data": output} if output else {}


def scrape_news(query: str) -> List[Dict]:
    """Scrapet News-Artikel."""
    output = run_agent_reach_command(f"agent-reach search '{query}'")
    
    try:
        if output.startswith("["):
            return json.loads(output)
    except:
        pass
    
    return []


def scrape_crunchbase(startup_name: str) -> str:
    """Scrapet Crunchbase-Profil."""
    return run_agent_reach_command(f"agent-reach search '{startup_name} site:crunchbase.com'")


def scrape_producthunt(startup_name: str) -> str:
    """Scrapet Product Hunt Listing."""
    return run_agent_reach_command(f"agent-reach search '{startup_name} site:producthunt.com'")


def scrape_kununu(startup_name: str) -> str:
    """Scrapet Kununu-Bewertungen für DACH-Kultur-Signale."""
    return run_agent_reach_command(f"agent-reach search '{startup_name} kununu bewertung erfahrung'")
