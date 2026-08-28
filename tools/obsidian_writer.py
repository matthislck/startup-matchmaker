"""
Obsidian Writer Tools

Funktionen zum Schreiben, Lesen und Organisieren von Markdown-Dateien
im Obsidian Vault für das Startup Matchmaker System.
"""

import os
from pathlib import Path
from typing import Dict
from datetime import datetime


def ensure_obsidian_structure(vault_path: str, startup_name: str) -> Dict[str, str]:
    """
    Erstellt die Ordnerstruktur für ein Startup im Obsidian Vault.
    
    Struktur:
    /startup-screening/
      /startups/{startup_name}/
        raw-data.md
        culture-profile.md
        match-analysis.md
        pitch-proposal.md
      /media/
        /podcasts/
        /interviews/
      profile.md (wenn nicht vorhanden, mit Template erstellen)
      feedback-log.md (wenn nicht vorhanden, mit Template erstellen)
    
    Args:
        vault_path: Pfad zum Obsidian Vault Root
        startup_name: Name des Startups (wird als Ordnername verwendet)
    
    Returns:
        Dict mit allen Dateipfaden für den weiteren Zugriff
    """
    # Basis-Pfade definieren
    base_dir = Path(vault_path) / "startup-screening"
    startups_dir = base_dir / "startups"
    startup_dir = startups_dir / startup_name
    media_dir = base_dir / "media"
    podcasts_dir = media_dir / "podcasts"
    interviews_dir = media_dir / "interviews"
    
    # Alle benötigten Ordner erstellen
    for directory in [base_dir, startups_dir, startup_dir, media_dir, podcasts_dir, interviews_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Datei-Pfade definieren
    file_paths = {
        "raw_data": str(startup_dir / "raw-data.md"),
        "culture_profile": str(startup_dir / "culture-profile.md"),
        "match_analysis": str(startup_dir / "match-analysis.md"),
        "pitch_proposal": str(startup_dir / "pitch-proposal.md"),
        "podcast_transcripts": str(podcasts_dir / f"{startup_name}-transcripts.md"),
        "interviews": str(interviews_dir / f"{startup_name}-interviews.md"),
        "profile": str(base_dir / "profile.md"),
        "feedback_log": str(base_dir / "feedback-log.md"),
    }
    
    # Profile.md erstellen wenn nicht vorhanden
    if not os.path.exists(file_paths["profile"]):
        profile_template = """# Mein Profil - Präferenzen für Startup-Praktikum

## Was mir wichtig ist

### Arbeitsweise
- [ ] Remote-First oder Hybrid
- [ ] Async Communication
- [ ] Flache Hierarchien
- [ ] Schnelle Entscheidungswege

### Tech-Stack Interessen
- [ ] AI/ML
- [ ] Product-Led Growth
- [ ] API-First
- [ ] Open Source

### Unternehmenskultur
- [ ] Transparente Kommunikation
- [ ] Learning Culture
- [ ] Customer-Centric
- [ ] Sustainable Growth

### Red Flags (Deal-Breaker)
- "Work hard, play hard" Mentalität
- Mikromanagement
- Keine klare Vision
- Hohe Fluktuation im Team

### Green Flags (Besonders attraktiv)
- Founder mit Operator-Erfahrung
- Klare Product-Market Fit Signale
- Dokumentation-first Kultur
- Internationale Ausrichtung

## Gewichtung der Kriterien
(1-10, wobei 10 am wichtigsten)

| Kriterium | Gewichtung | Notizen |
|-----------|------------|---------|
| Remote-Flexibilität | 8 | Wichtig für Work-Life-Balance |
| Tech-Stack Modernität | 7 | Will mit aktuellen Tools arbeiten |
| Gründer-Hintergrund | 9 | Erfahrung zählt mehr als Idee |
| Marktgröße | 6 | Sekundär, lerne lieber von besten |
| Funding-Status | 5 | Nicht entscheidend |

## Lernziele für das Praktikum

1. **Product Development**: Vom Customer Interview bis zum Feature Launch
2. **Growth Experiments**: A/B Testing, Analytics, Iteration
3. **Founder Mindset**: Entscheidungsfindung unter Unsicherheit
4. **Tech Skills**: Python Automation, AI Integration, No-Code Tools

## Bisheriges Feedback

<!-- Dieser Bereich wird vom Profile Updater Agent automatisch aktualisiert -->

"""
        save_to_obsidian(file_paths["profile"], profile_template)
    
    # Feedback-Log erstellen wenn nicht vorhanden
    if not os.path.exists(file_paths["feedback_log"]):
        feedback_template = """# Feedback Log

Dieses Dokument protokolliert alle Feedback-Einträge zu Startup-Analysen.
Das System nutzt dieses Feedback, um das Profil iterativ zu verbessern.

## Format

Jeder Eintrag enthält:
- Datum
- Startup Name
- Original Fit-Score & Begründung
- User Feedback (was war ungenau/falsch/wichtig)
- Abgeleitete Profil-Änderungen

---

"""
        save_to_obsidian(file_paths["feedback_log"], feedback_template)
    
    return file_paths


def save_to_obsidian(file_path: str, content: str) -> None:
    """
    Schreibt Content in eine Markdown-Datei.
    
    Args:
        file_path: Vollständiger Pfad zur Zieldatei
        content: Markdown-Content der geschrieben werden soll
    
    Note:
        Erstellt übergeordnete Verzeichnisse automatisch falls nötig.
    """
    # Stelle sicher, dass das Verzeichnis existiert
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Schreibe die Datei mit UTF-8 Encoding
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def read_from_obsidian(file_path: str) -> str:
    """
    Liest Content aus einer Markdown-Datei.
    
    Args:
        file_path: Vollständiger Pfad zur Quelldatei
    
    Returns:
        Inhalt der Datei als String
    
    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Die Datei '{file_path}' wurde nicht gefunden.")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def append_feedback(
    feedback_log_path: str,
    startup_name: str,
    original_reasoning: str,
    user_feedback: str
) -> None:
    """
    Fügt neues Feedback zum feedback-log.md hinzu.
    
    Args:
        feedback_log_path: Pfad zur feedback-log.md Datei
        startup_name: Name des bewerteten Startups
        original_reasoning: Die ursprüngliche Fit-Begründung des Systems
        user_feedback: Der Kommentar des Users zur Analyse
    
    Note:
        Fügt einen zeitgestempelten Eintrag im Markdown-Format hinzu.
        Das Format ist so gestaltet, dass es später vom Profile Updater
        geparst werden kann.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    feedback_entry = f"""
## [{timestamp}] {startup_name}

### Original Fit-Begründung
{original_reasoning}

### User Feedback
{user_feedback}

### Status
- [ ] Profil-Update abgeleitet
- [ ] In nextem Re-Match berücksichtigt

---

"""
    
    # Bestehenden Content lesen und neuen Eintrag anhängen
    existing_content = read_from_obsidian(feedback_log_path)
    updated_content = existing_content + feedback_entry
    save_to_obsidian(feedback_log_path, updated_content)
