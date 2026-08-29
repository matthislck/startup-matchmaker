"""
Robuster Scraping-Stack für DACH-Startup-Recherche.

Kombiniert mehrere spezialisierte APIs für maximale Zuverlässigkeit:
- Tavily API: Web-Suche (News, LinkedIn, Crunchbase)
- Jina Reader: Webseiten-Content extrahieren
- YouTube Transcript API: Podcast-Transkripte
- GitHub API: Tech-Stack Analyse
- Kununu Scraper: DACH-Kultur-Signale

Alle Funktionen haben umfassendes Error-Handling und fallen gracefully zurück.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import requests
from tavily import TavilyClient
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


# =============================================================================
# TAVILY WEB SEARCH
# =============================================================================

def tavily_search(query: str, api_key: str, search_depth: str = "advanced") -> List[Dict]:
    """
    Führt eine Websuche mit Tavily durch.
    
    Args:
        query: Suchanfrage
        api_key: Tavily API Key
        search_depth: "basic" oder "advanced"
    
    Returns:
        Liste von Suchergebnissen mit title, url, content
    """
    if not api_key:
        logger.warning("TAVILY_API_KEY nicht gesetzt")
        return []
    
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=10
        )
        
        results = []
        for result in response.get('results', []):
            results.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'content': result.get('content', '')[:1000],  # Limitiere Länge
                'score': result.get('score', 0)
            })
        
        logger.info(f"Tavily search für '{query}': {len(results)} Ergebnisse")
        return results
    
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []


def search_startup_general(startup_name: str, api_key: str) -> List[Dict]:
    """Allgemeine Suche nach Startup-Infos."""
    query = f"{startup_name} startup founder CEO team about"
    return tavily_search(query, api_key)


def search_startup_dach_news(startup_name: str, api_key: str) -> List[Dict]:
    """Spezifische Suche in DACH-News-Quellen."""
    query = f"{startup_name} (site:gruenderszene.de OR site:deutsche-startups.de OR site:omr.com OR site:handelsblatt.com OR site:wiwo.de)"
    return tavily_search(query, api_key)


def search_founders_impressum(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach Gründer-Infos via Impressum (DACH-spezifisch)."""
    query = f"{startup_name} impressum geschäftsführer gründer CEO founder"
    return tavily_search(query, api_key)


def search_crunchbase(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach Crunchbase-Profil."""
    query = f"{startup_name} site:crunchbase.com"
    return tavily_search(query, api_key)


def search_producthunt(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach Product Hunt Listing."""
    query = f"{startup_name} site:producthunt.com"
    return tavily_search(query, api_key)


def search_kununu(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach Kununu-Bewertungen (DACH-Kultur-Signale)."""
    query = f"{startup_name} kununu bewertung erfahrung mitarbeiter"
    return tavily_search(query, api_key)


def search_linkedin_company(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach LinkedIn Company Page."""
    query = f"{startup_name} site:linkedin.com/company"
    return tavily_search(query, api_key)


def search_twitter_founder(founder_name: str, api_key: str) -> List[Dict]:
    """Suche nach Twitter-Profil eines Gründers."""
    query = f"{founder_name} site:twitter.com OR site:x.com"
    return tavily_search(query, api_key)


def search_youtube_interviews(founder_name: str, startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach YouTube-Interviews/Podcasts."""
    query = f"{founder_name} {startup_name} interview podcast talk"
    return tavily_search(query, api_key)


def search_github_org(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach GitHub Organization."""
    query = f"{startup_name} site:github.com"
    return tavily_search(query, api_key)


def search_reddit_discussions(startup_name: str, api_key: str) -> List[Dict]:
    """Suche nach Reddit-Diskussionen."""
    query = f"{startup_name} site:reddit.com"
    return tavily_search(query, api_key)


# =============================================================================
# JINA READER - WEBPAGE CONTENT EXTRACTION
# =============================================================================

def jina_read_url(url: str, max_retries: int = 3) -> str:
    """
    Extrahiert cleanen Textinhalt einer Webseite via Jina Reader API.
    
    Args:
        url: Ziel-URL
        max_retries: Maximale Anzahl von Retry-Versuchen bei 429/503 Fehlern
    
    Returns:
        Extrahierter Textinhalt oder leerer String bei Fehler
    """
    if not url:
        return ""
    
    # User-Agent Rotation für bessere Akzeptanz
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    import random
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    retry_count = 0
    base_delay = 3  # Basis-Delay in Sekunden (erhöht für bessere Erfolgsrate)
    
    while retry_count <= max_retries:
        try:
            # Jina Reader Endpoint - mit X-Retry Header für besseres Handling
            jina_url = f"https://r.jina.ai/{url}"
            
            # Füge zusätzliche Jina-spezifische Header hinzu
            jina_headers = headers.copy()
            jina_headers["X-With-Generated-Alt"] = "true"  # Bessere Bildbeschreibungen
            jina_headers["X-With-Links-Summary"] = "false"  # Weniger Overhead
            
            response = requests.get(jina_url, headers=jina_headers, timeout=45)
            
            if response.status_code == 200:
                content = response.text.strip()
                logger.info(f"Jina Reader erfolgreich für: {url}")
                return content[:8000]  # Limitiere auf 8000 Zeichen
            
            elif response.status_code in [429, 503, 502]:
                # Rate Limiting oder Service Unavailable - Retry mit Backoff
                retry_delay = base_delay * (2 ** retry_count) + random.uniform(1, 3)
                logger.warning(f"Jina Reader rate limited for {url}: Status {response.status_code}. Retry {retry_count+1}/{max_retries} in {retry_delay:.1f}s")
                time.sleep(retry_delay)
                retry_count += 1
                
            elif response.status_code == 403:
                # Forbidden - oft bei zu vielen Requests vom gleichen IP
                # Versuche mit längerem Delay
                if retry_count < max_retries:
                    retry_delay = 5 + random.uniform(2, 5)
                    logger.warning(f"Jina Reader forbidden (403) for {url}. Retry {retry_count+1}/{max_retries} in {retry_delay:.1f}s")
                    time.sleep(retry_delay)
                    retry_count += 1
                else:
                    logger.error(f"Jina Reader permanently blocked (403) for {url}")
                    return f"[Fehler: Zugriff verweigert (403) - Website blockiert Anfragen]"
            
            else:
                logger.warning(f"Jina Reader failed for {url}: Status {response.status_code}")
                return f"[Fehler: HTTP {response.status_code} - Seite konnte nicht geladen werden]"
        
        except requests.exceptions.Timeout:
            logger.warning(f"Jina Reader timeout for {url}")
            if retry_count < max_retries:
                retry_delay = base_delay * (2 ** retry_count)
                time.sleep(retry_delay)
                retry_count += 1
            else:
                return "[Fehler: Timeout - Seite lädt zu langsam]"
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Jina Reader connection error for {url}: {e}")
            if retry_count < max_retries:
                retry_delay = base_delay * (2 ** retry_count)
                time.sleep(retry_delay)
                retry_count += 1
            else:
                return "[Fehler: Verbindungsproblem]"
        
        except Exception as e:
            logger.error(f"Jina Reader error: {e}")
            return f"[Fehler: {str(e)[:100]}]"
    
    # Alle Retries erschöpft
    logger.error(f"Jina Reader exhausted all retries for {url}")
    return f"[Fehler: Zu viele Anfragen - Bitte später erneut versuchen]"


def extract_website_content(website_url: str) -> Dict[str, str]:
    """
    Extrahiert Inhalte von verschiedenen Seiten einer Website.
    
    Args:
        website_url: Haupt-URL des Startups
    
    Returns:
        Dict mit homepage, about, team, blog, careers Inhalten
    """
    if not website_url:
        return {}
    
    # Normalisiere URL (entferne trailing slash)
    website_url = website_url.rstrip('/')
    
    # Erweiterte Liste von möglichen Seiten inkl. alternativer Pfade
    pages_to_scrape = {
        'homepage': website_url,
        'about': [f"{website_url}/about", f"{website_url}/about-us", f"{website_url}/company"],
        'team': [f"{website_url}/team", f"{website_url}/leadership", f"{website_url}/management"],
        'blog': [f"{website_url}/blog", f"{website_url}/news", f"{website_url}/press"],
        'careers': [f"{website_url}/careers", f"{website_url}/jobs", f"{website_url}/work-with-us"],
        'impressum': [f"{website_url}/impressum", f"{website_url}/legal", f"{website_url}/imprint"]  # DACH-spezifisch
    }
    
    results = {}
    
    for page_name, urls in pages_to_scrape.items():
        content = ""
        
        # Wenn page_name 'homepage' ist, ist urls ein String, keine Liste
        if page_name == 'homepage':
            urls = [urls]
        
        for url in urls:
            try:
                content = jina_read_url(url)
                if content and len(content) > 100 and "Vercel Security Checkpoint" not in content:  # Nur sinnvolle Inhalte speichern
                    results[page_name] = content
                    logger.info(f"Successfully scraped {page_name} from: {url}")
                    break  # Erfolg, breche ab und versuche nicht weitere URLs
                else:
                    logger.debug(f"No valid content from {url}")
            except Exception as e:
                logger.warning(f"Failed to scrape {page_name} from {url}: {e}")
            
            # Rate limiting zwischen Requests
            time.sleep(0.5)
        
        # Falls keine gültigen Inhalte gefunden wurden
        if page_name not in results:
            results[page_name] = ""
    
    return results


# =============================================================================
# YOUTUBE TRANSCRIPT API
# =============================================================================

def extract_video_id(youtube_url: str) -> Optional[str]:
    """
    Extrahiert Video-ID aus YouTube-URL.
    
    Args:
        youtube_url: YouTube URL (verschiedene Formate)
    
    Returns:
        Video-ID oder None
    """
    if not youtube_url:
        return None
    
    try:
        # Format: https://www.youtube.com/watch?v=VIDEO_ID
        if "watch?v=" in youtube_url:
            parsed = urlparse(youtube_url)
            params = parse_qs(parsed.query)
            return params.get('v', [None])[0]
        
        # Format: https://youtu.be/VIDEO_ID
        elif "youtu.be/" in youtube_url:
            parsed = urlparse(youtube_url)
            return parsed.path.lstrip('/')
        
        # Format: https://www.youtube.com/embed/VIDEO_ID
        elif "/embed/" in youtube_url:
            parsed = urlparse(youtube_url)
            return parsed.path.split('/')[-1]
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        return None


def get_youtube_transcript(video_url: str, languages: List[str] = ['de', 'en']) -> str:
    """
    Extrahiert Transkript von einem YouTube-Video.
    
    Args:
        video_url: YouTube URL
        languages: Bevorzugte Sprachen (de zuerst für DACH)
    
    Returns:
        Transkript als Text oder leerer String
    """
    video_id = extract_video_id(video_url)
    
    if not video_id:
        logger.warning(f"Invalid YouTube URL: {video_url}")
        return ""
    
    try:
        # Versuche Transkript in bevorzugten Sprachen zu extrahieren
        for lang in languages:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Suche manuell nach dem gewünschten Sprachcode
                for transcript in transcript_list:
                    if transcript.language_code.startswith(lang):
                        transcript_data = transcript.fetch()
                        
                        # Formatiere Transkript als fortlaufenden Text
                        full_text = " ".join([entry['text'] for entry in transcript_data])
                        logger.info(f"YouTube transcript extracted ({lang}): {video_id}")
                        return full_text
                
            except Exception:
                continue
        
        # Wenn keine spezifische Sprache gefunden wurde, versuche irgendein Transkript
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            first_transcript = next(iter(transcript_list))
            transcript_data = first_transcript.fetch()
            full_text = " ".join([entry['text'] for entry in transcript_data])
            logger.info(f"YouTube transcript extracted (auto): {video_id}")
            return full_text
        except Exception:
            pass
        
        logger.warning(f"No transcript available for: {video_id}")
        return ""
    
    except Exception as e:
        logger.error(f"YouTube transcript error: {e}")
        return ""


# =============================================================================
# GITHUB API
# =============================================================================

def analyze_github_organization(org_name: str, github_token: Optional[str] = None) -> Dict:
    """
    Analysiert GitHub Organization eines Startups.
    
    Args:
        org_name: Name der GitHub Organization
        github_token: Optionaler GitHub Token für höhere Rate Limits
    
    Returns:
        Dict mit Org-Infos, Repos, Tech-Stack
    """
    if not org_name:
        return {}
    
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    base_url = f"https://api.github.com/orgs/{org_name}"
    
    try:
        # Hole Organization Info
        org_response = requests.get(base_url, headers=headers, timeout=10)
        
        if org_response.status_code != 200:
            logger.warning(f"GitHub org not found: {org_name}")
            return {"error": "Organization not found", "org_name": org_name}
        
        org_data = org_response.json()
        
        # Hole Repositories
        repos_response = requests.get(
            f"{base_url}/repos",
            headers=headers,
            params={'per_page': 20, 'sort': 'updated'},
            timeout=10
        )
        
        repos = []
        tech_stack = set()
        
        if repos_response.status_code == 200:
            repos_data = repos_response.json()
            
            for repo in repos_data[:10]:  # Top 10 Repos
                repo_info = {
                    'name': repo['name'],
                    'description': repo.get('description', ''),
                    'language': repo.get('language', 'Unknown'),
                    'stars': repo.get('stargazers_count', 0),
                    'forks': repo.get('forks_count', 0),
                    'updated_at': repo.get('updated_at', ''),
                    'url': repo.get('html_url', '')
                }
                repos.append(repo_info)
                
                # Tech-Stack extrahieren
                if repo_info['language']:
                    tech_stack.add(repo_info['language'])
        
        result = {
            'org_name': org_name,
            'org_url': org_data.get('html_url', ''),
            'description': org_data.get('description', ''),
            'created_at': org_data.get('created_at', ''),
            'public_repos': org_data.get('public_repos', 0),
            'followers': org_data.get('followers', 0),
            'repos': repos,
            'tech_stack': list(tech_stack),
            'scraped_at': datetime.now().isoformat()
        }
        
        logger.info(f"GitHub analysis complete for: {org_name}")
        return result
    
    except Exception as e:
        logger.error(f"GitHub API error: {e}")
        return {"error": str(e), "org_name": org_name}


# =============================================================================
# COMPREHENSIVE STARTUP SCRAPING
# =============================================================================

def scrape_startup_comprehensive(
    startup_name: str,
    founder_names: Optional[List[str]] = None,
    website_url: Optional[str] = None
) -> Dict:
    """
    Umfassendes Scraping aller verfügbaren Quellen für ein Startup.
    
    Args:
        startup_name: Name des Startups
        founder_names: Optionale Liste von Gründer-Namen
        website_url: Optionale Website-URL
    
    Returns:
        Umfassendes Dict mit allen gesammelten Daten
    """
    logger.info(f"Starting comprehensive scrape for: {startup_name}")
    
    # API Keys laden
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")
    github_token = os.getenv("GITHUB_TOKEN", "")
    
    raw_data = {
        'startup_name': startup_name,
        'scraped_at': datetime.now().isoformat(),
        'sources_count': 0,
        'data_quality': 'unknown',
        'founders': [],
        'website': {},
        'news': [],
        'social_media': {},
        'youtube_interviews': [],
        'github': {},
        'reddit': [],
        'kununu': [],
        'crunchbase': [],
        'producthunt': []
    }
    
    # ========================================
    # 1. WEBSITE CONTENT (Jina Reader)
    # ========================================
    if not website_url:
        # Versuche Website-URL via Tavily Search zu finden (zuverlässiger als Raten)
        logger.info(f"Searching for official website of {startup_name}...")
        search_results = tavily_search(f"{startup_name} official website", tavily_api_key, search_depth="basic")
        
        if search_results:
            # Nimm das erste relevante Ergebnis als Website-URL
            for result in search_results[:5]:
                url = result.get('url', '')
                content_preview = result.get('content', '')
                
                # Filtere nur relevante Domains (keine Social Media, keine Verzeichnisse)
                if any(domain in url for domain in ['linkedin.com', 'twitter.com', 'facebook.com', 'youtube.com', 'crunchbase.com', 'producthunt.com', 'kununu.com', 'glassdoor.com']):
                    continue
                
                # Prüfe ob URL zur Hauptdomain gehört (Wikipedia, TechCrunch, etc. enthalten oft die echte URL)
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                
                # Extrahiere die Hauptdomain aus Suchergebnissen
                # Beispiel: wenn Content "www.personio.de" enthält, nutze das
                import re
                url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-z]{2,6})(?:/|$)'
                matches = re.findall(url_pattern, content_preview.lower())
                
                if matches:
                    # Nehme die erste gefundene Domain die nicht Social Media ist
                    for match in matches:
                        if match not in ['linkedin.com', 'twitter.com', 'facebook.com', 'youtube.com', 'crunchbase.com', 'producthunt.com']:
                            test_url = f"https://{match}"
                            content = jina_read_url(test_url)
                            if content and len(content) > 200 and "Vercel Security Checkpoint" not in content and "429" not in content:
                                website_url = test_url
                                logger.info(f"Found official website from search result: {website_url}")
                                break
                    
                    if website_url:
                        break
        
        # Fallback: Versuche URL zu erraten wenn Suche nichts fand
        if not website_url:
            possible_urls = [
                f"https://{startup_name.lower().replace(' ', '')}.com",
                f"https://{startup_name.lower().replace(' ', '-')}.com",
                f"https://{startup_name.lower().replace(' ', '')}.de",
                f"https://{startup_name.lower().replace(' ', '')}.io",
                f"https://www.{startup_name.lower().replace(' ', '')}.com",
                f"https://www.{startup_name.lower().replace(' ', '')}.de"
            ]
            
            for url in possible_urls:
                content = jina_read_url(url, max_retries=1)  # Schnell testen mit nur 1 Retry
                if content and len(content) > 200 and "Vercel Security Checkpoint" not in content and "429" not in content:
                    website_url = url
                    logger.info(f"Guessed working website: {website_url}")
                    break
    
    if website_url:
        raw_data['website'] = extract_website_content(website_url)
        raw_data['sources_count'] += 1
        logger.info(f"Website scraped: {website_url}")
    else:
        logger.warning(f"Could not find valid website for {startup_name}")
        # Speichere Info dass Website nicht gefunden wurde
        raw_data['website'] = {'error': 'Website not found or blocked'}
    
    # ========================================
    # 2. ALLGEMEINE SUCHE & GRÜNDER-IDENTIFIKATION
    # ========================================
    general_results = search_startup_general(startup_name, tavily_api_key)
    impressum_results = search_founders_impressum(startup_name, tavily_api_key)
    
    # Extrahiere Founder-Namen aus den Ergebnissen (einfache Heuristik)
    if not founder_names and (general_results or impressum_results):
        # Hinweis: Hier könnte ein LLM zur Extraktion verwendet werden
        # Für jetzt speichern wir nur die Suchergebnisse
        raw_data['founder_search_results'] = {
            'general': general_results,
            'impressum': impressum_results
        }
        raw_data['sources_count'] += 2
    
    # ========================================
    # 3. DACH-NEWS
    # ========================================
    dach_news = search_startup_dach_news(startup_name, tavily_api_key)
    if dach_news:
        raw_data['news'] = dach_news
        raw_data['sources_count'] += 1
        logger.info(f"DACH News found: {len(dach_news)} articles")
    
    # ========================================
    # 4. KUNUNU (DACH-Kultur-Signale)
    # ========================================
    kununu_results = search_kununu(startup_name, tavily_api_key)
    if kununu_results:
        raw_data['kununu'] = kununu_results
        raw_data['sources_count'] += 1
        logger.info(f"Kununu reviews found: {len(kununu_results)}")
    
    # ========================================
    # 5. CRUNCHBASE & PRODUCT HUNT
    # ========================================
    crunchbase_results = search_crunchbase(startup_name, tavily_api_key)
    if crunchbase_results:
        raw_data['crunchbase'] = crunchbase_results
        raw_data['sources_count'] += 1
    
    producthunt_results = search_producthunt(startup_name, tavily_api_key)
    if producthunt_results:
        raw_data['producthunt'] = producthunt_results
        raw_data['sources_count'] += 1
    
    # ========================================
    # 6. LINKEDIN COMPANY
    # ========================================
    linkedin_results = search_linkedin_company(startup_name, tavily_api_key)
    if linkedin_results:
        raw_data['social_media']['linkedin_company'] = linkedin_results
        raw_data['sources_count'] += 1
    
    # ========================================
    # 7. FÜR JEDEN GRÜNDER: Twitter, YouTube
    # ========================================
    if founder_names:
        for founder in founder_names:
            founder_data = {}
            
            # Twitter
            twitter_results = search_twitter_founder(founder, tavily_api_key)
            if twitter_results:
                founder_data['twitter'] = twitter_results
                raw_data['sources_count'] += 1
            
            # YouTube Interviews
            youtube_results = search_youtube_interviews(founder, startup_name, tavily_api_key)
            if youtube_results:
                # Extrahiere Transkripte für die ersten 2 Videos
                for video in youtube_results[:2]:
                    transcript = get_youtube_transcript(video['url'])
                    video['transcript'] = transcript
                    video['transcript_length'] = len(transcript) if transcript else 0
                
                founder_data['youtube'] = youtube_results
                raw_data['sources_count'] += 1
            
            raw_data['social_media'][f'founder_{founder.replace(" ", "_").lower()}'] = founder_data
    
    # ========================================
    # 8. GITHUB ORGANIZATION
    # ========================================
    github_results = search_github_org(startup_name, tavily_api_key)
    if github_results:
        # Extrahiere Org-Name aus Suchergebnissen
        for result in github_results:
            if 'github.com' in result['url']:
                # Versuche Org-Name zu extrahieren
                parts = result['url'].split('github.com/')
                if len(parts) > 1:
                    org_name = parts[1].split('/')[0]
                    github_analysis = analyze_github_organization(org_name, github_token)
                    if github_analysis:
                        raw_data['github'] = github_analysis
                        break
        
        raw_data['sources_count'] += 1
    
    # ========================================
    # 9. REDDIT DISCUSSIONS
    # ========================================
    reddit_results = search_reddit_discussions(startup_name, tavily_api_key)
    if reddit_results:
        raw_data['reddit'] = reddit_results
        raw_data['sources_count'] += 1
    
    # ========================================
    # DATENQUALITÄT BEWERTEN
    # ========================================
    sources_count = raw_data['sources_count']
    if sources_count >= 8:
        raw_data['data_quality'] = 'high'
    elif sources_count >= 5:
        raw_data['data_quality'] = 'medium'
    else:
        raw_data['data_quality'] = 'low'
    
    logger.info(f"Comprehensive scrape completed. Quality: {raw_data['data_quality']} ({sources_count} sources)")
    
    return raw_data


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_for_llm(scraped_data: Dict) -> str:
    """
    Formatiert gescrapte Daten für LLM-Kontext.
    
    Args:
        scraped_data: Rohdaten aus scrape_startup_comprehensive
    
    Returns:
        Formatierter String für LLM-Input (max. 8000 Zeichen)
    """
    md = f"# Startup Analyse: {scraped_data.get('startup_name', 'Unknown')}\n\n"
    md += f"*Datenqualität: {scraped_data.get('data_quality', 'unknown').upper()}*\n"
    md += f"*Quellen: {scraped_data.get('sources_count', 0)}*\n\n"
    
    # Website
    if scraped_data.get('website'):
        md += "## Website\n\n"
        website = scraped_data['website']
        if website.get('homepage'):
            md += f"**Homepage:** {website['homepage'][:800]}...\n\n"
        if website.get('about'):
            md += f"**About:** {website['about'][:800]}...\n\n"
        if website.get('team'):
            md += f"**Team:** {website['team'][:800]}...\n\n"
    
    # News
    if scraped_data.get('news'):
        md += "## News & Presse\n\n"
        for article in scraped_data['news'][:5]:
            md += f"- **{article.get('title', 'Unknown')}** ({article.get('url', '')})\n"
            md += f"  {article.get('content', '')[:200]}...\n\n"
    
    # Kununu
    if scraped_data.get('kununu'):
        md += "## Kununu Bewertungen\n\n"
        for review in scraped_data['kununu'][:3]:
            md += f"- **{review.get('title', 'Unknown')}**\n"
            md += f"  {review.get('content', '')[:300]}...\n\n"
    
    # YouTube Interviews
    if scraped_data.get('youtube_interviews'):
        md += "## YouTube Interviews\n\n"
        for interview in scraped_data['youtube_interviews'][:3]:
            md += f"### {interview.get('title', 'Unknown')}\n"
            md += f"**URL:** {interview.get('url', '')}\n"
            if interview.get('transcript'):
                md += f"**Transkript:** {interview['transcript'][:1000]}...\n\n"
    
    # GitHub
    if scraped_data.get('github') and not scraped_data['github'].get('error'):
        github = scraped_data['github']
        md += "## GitHub\n\n"
        md += f"**Org:** {github.get('org_name', 'N/A')}\n"
        md += f"**Tech Stack:** {', '.join(github.get('tech_stack', []))}\n"
        md += f"**Repos:** {github.get('public_repos', 0)}\n\n"
    
    # Limitiere Gesamtlänge auf 8000 Zeichen
    if len(md) > 8000:
        md = md[:8000] + "\n\n... (gekürzt aufgrund von Kontext-Limit)"
    
    return md
