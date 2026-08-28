from typing import TypedDict, Optional, Dict, List


class AgentState(TypedDict):
    """
    Zentraler State für das Multi-Agenten-System.
    
    Wird durch alle Nodes im LangGraph gereicht und enthält:
    - Input-Daten (startup_name)
    - Zwischenergebnisse (raw_data, culture_profile)
    - Bewertungsergebnisse (fit_score, fit_reasoning)
    - User-Interaktion (user_feedback)
    - Output (pitch_draft, obsidian_paths)
    """
    startup_name: str
    raw_data: Dict  # scraped content, transcripts, posts
    culture_profile: Dict  # extracted philosophy, values, red/green flags
    fit_score: int  # 0-100
    fit_reasoning: str  # detailed explanation
    user_feedback: Optional[str]  # comments on reasoning
    pitch_draft: Optional[str]  # generated door opener
    obsidian_paths: Dict[str, str]  # file paths for markdown outputs
