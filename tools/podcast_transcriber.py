"""
Podcast Transcriber Tools

Funktionen zum Finden und Transkribieren von Podcast-Episoden
mit Gründern oder über Startups. Besonders wertvoll für die Kultur-Analyse.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime


def find_podcast_episodes(startup_name: str) -> List[Dict]:
    """
    Sucht nach Podcast-Episoden mit dem Startup/Gründer.
    
    Quellen:
    - Apple Podcasts Search (via Web Search)
    - Spotify (via Web Search)
    - YouTube (Founder Interviews)
    - Deutsche Podcast-Plattformen (z.B. OMR Podcast, Gründerszene)
    
    Args:
        startup_name: Name des Startups oder der Gründer
    
    Returns:
        List von Dicts mit:
        {
            "title": str,
            "url": str,
            "duration": Optional[str],
            "platform": str,  # "spotify", "apple", "youtube", etc.
            "description": str,
            "founder_mentioned": str,
            "date": Optional[str]
        }
    
    Note:
        Nutzt primär Web Search, da direkte API-Zugriffe auf
        Podcast-Plattformen oft kostenpflichtig oder limitiert sind.
        Die eigentliche Audio-Verarbeitung erfolgt in transcribe_podcast().
    """
    episodes = []
    
    # Tavily API für Websuche verwenden
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if not tavily_api_key:
        # Fallback: manuelle Suche simulieren (für Development)
        return [{
            "title": f"Podcast-Suche benötigt TAVILY_API_KEY",
            "url": "",
            "platform": "error",
            "description": "Bitte setze TAVILY_API_KEY in deiner .env Datei",
            "founder_mentioned": startup_name
        }]
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_api_key)
    except ImportError:
        return [{
            "title": "Tavily Client nicht installiert",
            "url": "",
            "platform": "error",
            "description": "pip install tavily-python",
            "founder_mentioned": startup_name
        }]
    
    # 1. Allgemeine Podcast-Suche
    search_queries = [
        f"{startup_name} podcast interview german",
        f"{startup_name} founder podcast episode",
        f"{startup_name} gründerszene podcast",
        f"{startup_name} OMR podcast interview",
    ]
    
    for query in search_queries:
        try:
            response = client.search(query, search_depth="basic", max_results=5)
            
            for item in response.get("results", []):
                url = item.get("url", "")
                title = item.get("title", "")
                content = item.get("content", "")
                
                # Plattform identifizieren
                platform = "unknown"
                if "spotify.com" in url:
                    platform = "spotify"
                elif "podcasts.apple.com" in url:
                    platform = "apple"
                elif "youtube.com" in url or "youtu.be" in url:
                    platform = "youtube"
                elif "open.spotify.com" in url:
                    platform = "spotify"
                
                # Nur relevante Ergebnisse hinzufügen
                if platform != "unknown" or any(kw in url.lower() for kw in ["podcast", "interview"]):
                    episode = {
                        "title": title,
                        "url": url,
                        "duration": None,  # Wird später extrahiert wenn möglich
                        "platform": platform,
                        "description": content,
                        "founder_mentioned": startup_name,
                        "date": None,
                        "search_query": query
                    }
                    
                    # Vermeide Duplikate
                    if not any(e["url"] == url for e in episodes):
                        episodes.append(episode)
        
        except Exception as e:
            # Bei Fehlern einfach weitermachen mit nächster Query
            continue
    
    # Sortiere nach Relevanz (Podcast-Plattformen zuerst)
    platform_priority = {"spotify": 1, "apple": 2, "youtube": 3, "unknown": 4}
    episodes.sort(key=lambda x: platform_priority.get(x["platform"], 4))
    
    return episodes


def transcribe_podcast(audio_url: str, api_key: Optional[str] = None) -> str:
    """
    Transkribiert eine Podcast-Episode.
    
    Nutzt:
    - Whisper API (wenn Audio-URL direkt verfügbar)
    - Oder sucht nach existierenden Transkripten im Web
    - Fallback: Zusammenfassung aus Show Notes
    
    Args:
        audio_url: URL zur Audio-Datei oder Podcast-Episode
        api_key: OpenAI API Key für Whisper (optional)
    
    Returns:
        Transkript als Text. Bei Fehlern eine aussagekräftige Fehlermeldung.
    
    Note:
        Direkte Audio-Transkription erfordert:
        1. Dass die URL direkt zur Audio-Datei führt (nicht zur Player-Seite)
        2. Download der Audio-Datei
        3. Whisper API Call
        
        In den meisten Fällen suchen wir stattdessen nach:
        - Existierenden Transkripten auf der Website
        - Show Notes mit detaillierten Inhalten
        - Blog Posts zur Episode
    """
    
    # Prüfen ob es sich um eine direkte Audio-URL handelt
    audio_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
    is_direct_audio = any(audio_url.endswith(ext) for ext in audio_extensions)
    
    if is_direct_audio:
        # Versuch mit Whisper API zu transkribieren
        return _transcribe_with_whisper(audio_url, api_key)
    else:
        # Suche nach existierenden Transkripten oder Show Notes
        return _find_existing_transcript(audio_url)


def _transcribe_with_whisper(audio_url: str, api_key: Optional[str] = None) -> str:
    """
    Interne Funktion: Transkribiert Audio mit Whisper API.
    
    Args:
        audio_url: Direkter Link zur Audio-Datei
        api_key: OpenAI API Key
    
    Returns:
        Vollständiges Transkript
    """
    
    openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        return "[FEHLER] Keine OpenAI API Key gefunden. Whisper-Transkription nicht möglich."
    
    try:
        import requests
        from openai import OpenAI
        
        # Audio-Datei herunterladen
        response = requests.get(audio_url, timeout=30)
        if response.status_code != 200:
            return f"[FEHLER] Audio-Download fehlgeschlagen: Status {response.status_code}"
        
        # Temporäre Datei erstellen
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        
        # Whisper API aufrufen
        client = OpenAI(api_key=openai_api_key)
        
        with open(tmp_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="de"  # Primär Deutsch für DACH-Startups
            )
        
        # Aufräumen
        import os
        os.unlink(tmp_file_path)
        
        return transcription.text
    
    except ImportError as e:
        return f"[FEHLER] Benötigte Pakete nicht installiert: {str(e)}"
    except Exception as e:
        return f"[FEHLER] Whisper-Transkription fehlgeschlagen: {str(e)}"


def _find_existing_transcript(podcast_url: str) -> str:
    """
    Interne Funktion: Sucht nach existierenden Transkripten im Web.
    
    Args:
        podcast_url: URL zur Podcast-Episode (Webseite, nicht Audio)
    
    Returns:
        Gefundenes Transkript oder Show Notes
    """
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if not tavily_api_key:
        return "[INFO] Keine Tavily API Key. Suche nach Transkripten übersprungen."
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_api_key)
        
        # Suche nach Transkript zur spezifischen Episode
        search_query = f"transcript {podcast_url}"
        response = client.search(search_query, search_depth="basic", max_results=5)
        
        transcripts_found = []
        for item in response.get("results", []):
            content = item.get("content", "")
            if len(content) > 100:  # Nur substanzielle Inhalte
                transcripts_found.append(content)
        
        if transcripts_found:
            # Kombiniere gefundene Transkript-Abschnitte
            return "\n\n---\n\n".join(transcripts_found[:3])  # Max 3 Abschnitte
        else:
            return f"[INFO] Kein direktes Transkript gefunden für: {podcast_url}\n\nHinweis: Manuelle Transkription mit Whisper API empfohlen."
    
    except Exception as e:
        return f"[FEHLER] Suche nach Transkript fehlgeschlagen: {str(e)}"


def get_youtube_transcript(video_id: str) -> Optional[str]:
    """
    Versucht ein YouTube-Transkript zu extrahieren.
    
    Args:
        video_id: YouTube Video ID (z.B. "dQw4w9WgXcQ")
    
    Returns:
        Transkript wenn verfügbar, sonst None
    
    Note:
        Diese Funktion nutzt die youtube-transcript-api wenn installiert.
        Ist optional und wird nur verwendet wenn andere Methoden scheitern.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
        
        # Transcript-Text zusammenfügen
        full_text = " ".join([entry['text'] for entry in transcript])
        return full_text
    
    except ImportError:
        return None  # Paket nicht installiert, kein Problem
    except Exception:
        return None  # Transcript nicht verfügbar für dieses Video
