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

from .scraping_stack import (
    scrape_startup_comprehensive,
    format_for_llm,
    get_youtube_transcript
)

__all__ = [
    # Obsidian
    "ensure_obsidian_structure",
    "save_to_obsidian",
    "read_from_obsidian",
    "append_feedback",
    
    # Web Scraping (neuer Stack)
    "scrape_startup_comprehensive",
    "format_for_llm",
    
    # Podcasts
    "get_youtube_transcript",
]
