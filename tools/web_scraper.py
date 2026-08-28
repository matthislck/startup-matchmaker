"""
Web Scraper Tools

Funktionen zum Sammeln von Startup-Daten aus verschiedenen Online-Quellen
unter Verwendung der Tavily API und anderen Web-Scraping-Methoden.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime


def scrape_startup_data(startup_name: str, api_key: Optional[str] = None) -> Dict:
    """
    Sammelt Daten über ein Startup aus verschiedenen Quellen.
    
    Nutzt Tavily API für:
    - Website (About, Team, Blog)
    - LinkedIn Posts der Gründer
    - News-Artikel (Gründerszene, TechCrunch)
    - Job Postings
    
    Args:
        startup_name: Name des Startups zu recherchieren
        api_key: Tavily API Key (fallback zu env variable)
    
    Returns:
        Dict mit strukturierten Daten:
        {
            "company_info": {...},
            "founders": [...],
            "news_articles": [...],
            "job_postings": [...],
            "social_media": {...},
            "tech_stack": [...],
            "funding_info": {...},
            "timestamp": "..."
        }
    
    Note:
        Bei API-Fehlern wird ein leeres Dict mit Fehlerinformation zurückgegeben,
        statt einer Exception, um den Agenten-Flow nicht zu unterbrechen.
    """
    # API Key holen
    tavily_api_key = api_key or os.getenv("TAVILY_API_KEY")
    
    if not tavily_api_key:
        return {
            "error": "Kein Tavily API Key gefunden. Setze TAVILY_API_KEY in .env",
            "startup_name": startup_name,
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_api_key)
    except ImportError:
        return {
            "error": "Tavily Python Client nicht installiert. pip install tavily-python",
            "startup_name": startup_name,
            "timestamp": datetime.now().isoformat()
        }
    
    # Initialisiere Ergebnis-Struktur
    result = {
        "startup_name": startup_name,
        "company_info": {},
        "founders": [],
        "news_articles": [],
        "job_postings": [],
        "social_media": {},
        "tech_stack": [],
        "funding_info": {},
        "podcasts_interviews": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # 1. Allgemeine Unternehmenssuche
    try:
        search_query = f"{startup_name} startup company about team mission"
        response = client.search(search_query, search_depth="advanced", max_results=10)
        
        for item in response.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")
            content = item.get("content", "")
            
            # Kategorisiere die Ergebnisse basierend auf URL/Inhalt
            if "linkedin.com" in url:
                if "jobs" in url:
                    result["job_postings"].append({
                        "title": title,
                        "url": url,
                        "description": content,
                        "source": "LinkedIn"
                    })
                else:
                    result["social_media"]["linkedin"] = {
                        "url": url,
                        "content": content
                    }
            elif "twitter.com" in url or "x.com" in url:
                result["social_media"]["twitter"] = {
                    "url": url,
                    "content": content
                }
            elif any(keyword in url for keyword in ["gruenderszene", "deutsche-startups", "omr", "handelsblatt"]):
                result["news_articles"].append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "source": "DACH News",
                    "date": datetime.now().isoformat()
                })
            elif any(keyword in url for keyword in ["techcrunch", "bloomberg", "reuters"]):
                result["news_articles"].append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "source": "International News",
                    "date": datetime.now().isoformat()
                })
            else:
                # Vermutlich Company Website oder About-Seite
                if not result["company_info"]:
                    result["company_info"] = {
                        "website": url,
                        "description": content,
                        "mission": content[:500] if len(content) > 500 else content
                    }
    except Exception as e:
        result["errors"] = result.get("errors", [])
        result["errors"].append(f"Fehler bei allgemeiner Suche: {str(e)}")
    
    # 2. Spezifische Gründer-Suche
    try:
        founders_query = f"{startup_name} founder CEO co-founder interview"
        response = client.search(founders_query, search_depth="basic", max_results=5)
        
        for item in response.get("results", []):
            result["founders"].append({
                "source_url": item.get("url"),
                "title": item.get("title"),
                "snippet": item.get("content")
            })
    except Exception as e:
        result["errors"] = result.get("errors", [])
        result["errors"].append(f"Fehler bei Gründer-Suche: {str(e)}")
    
    # 3. Podcast & Interview Suche (wichtig für Kultur-Analyse!)
    try:
        podcast_query = f"{startup_name} podcast interview founder audio transcript"
        response = client.search(podcast_query, search_depth="advanced", max_results=10)
        
        for item in response.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")
            content = item.get("content", "")
            
            # Prüfen ob es sich um Podcast/Interview handelt
            if any(keyword in url.lower() for keyword in ["spotify", "apple.com/podcast", "youtube", "podcast"]):
                result["podcasts_interviews"].append({
                    "title": title,
                    "url": url,
                    "description": content,
                    "type": "podcast" if "podcast" in url.lower() else "interview"
                })
    except Exception as e:
        result["errors"] = result.get("errors", [])
        result["errors"].append(f"Fehler bei Podcast-Suche: {str(e)}")
    
    # 4. Funding & Investment Info
    try:
        funding_query = f"{startup_name} funding investment round series A B C valuation"
        response = client.search(funding_query, search_depth="basic", max_results=5)
        
        funding_snippets = []
        for item in response.get("results", []):
            funding_snippets.append({
                "source": item.get("url"),
                "title": item.get("title"),
                "content": item.get("content")
            })
        
        if funding_snippets:
            result["funding_info"] = {
                "snippets": funding_snippets,
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        result["errors"] = result.get("errors", [])
        result["errors"].append(f"Fehler bei Funding-Suche: {str(e)}")
    
    # 5. Tech Stack Recherche
    try:
        tech_query = f"{startup_name} tech stack technology programming language tools"
        response = client.search(tech_query, search_depth="basic", max_results=5)
        
        tech_mentions = []
        for item in response.get("results", []):
            tech_mentions.append({
                "source": item.get("url"),
                "snippet": item.get("content")
            })
        
        if tech_mentions:
            result["tech_stack"] = tech_mentions
    except Exception as e:
        result["errors"] = result.get("errors", [])
        result["errors"].append(f"Fehler bei Tech-Stack-Suche: {str(e)}")
    
    return result
