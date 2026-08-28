"""
Tools Package

Obsidian-Integration und Data Collection Tools für das Startup Matchmaker System.
"""

from .obsidian_writer import (
    ensure_obsidian_structure,
    save_to_obsidian,
    read_from_obsidian,
    append_feedback
)

from .web_scraper import (
    scrape_startup_data
)

from .podcast_transcriber import (
    find_podcast_episodes,
    transcribe_podcast,
    get_youtube_transcript
)

__all__ = [
    # Obsidian
    "ensure_obsidian_structure",
    "save_to_obsidian",
    "read_from_obsidian",
    "append_feedback",
    
    # Web Scraping
    "scrape_startup_data",
    
    # Podcasts
    "find_podcast_episodes",
    "transcribe_podcast",
    "get_youtube_transcript",
]
