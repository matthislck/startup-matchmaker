# DACH Startup Matchmaker & Pitch Agent System

Ein Multi-Agenten-System, das automatisch Startups im deutschsprachigen Raum (DACH: Deutschland, Österreich, Schweiz) recherchiert, analysiert und bewertet, ob sie zu deinen persönlichen Präferenzen passen. Wenn ein Match gut ist, generiert das System einen maßgeschneiderten "Door Opener" Projektvorschlag für eine Praktikumsbewerbung.

## Features

- **Automatisierte Recherche**: Scout Agent sammelt Daten aus Website, LinkedIn, Podcasts, Interviews, News und Job Postings
- **Kultur-Analyse**: Profiler Agent extrahiert Werte, Kommunikationsstil und identifiziert Red/Green Flags
- **Iteratives Matching**: Matchmaker Agent vergleicht Startup-Profil mit deinen Präferenzen (Fit-Score 0-100)
- **Pitch-Generierung**: Pitch Architect erstellt Door-Opener-Projektvorschläge bei gutem Fit (≥70)
- **Feedback-Loop**: Profile Updater lernt aus deinem Feedback und verbessert zukünftige Matches
- **Obsidian-First**: Alle Outputs sind Markdown-Dateien in strukturierter Ordnerhierarchie

## Installation

```bash
pip install -r requirements.txt
```

## Konfiguration

1. Kopiere `.env.example` nach `.env`:
```bash
cp .env.example .env
```

2. Füge deine API-Keys hinzu:
```
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

## Usage

### Erstmaliges Screening

```bash
python main.py --startup "n8n"
```

Das System erstellt alle Dateien in deinem Obsidian Vault unter `/startup-screening/startups/n8n/`:
- `raw-data.md` – Gesammelte Rohdaten
- `culture-profile.md` – Kultur-Analyse mit Red/Green Flags
- `match-analysis.md` – Fit-Score und Begründung
- `pitch-proposal.md` – Door-Opener Vorschlag (nur wenn Fit ≥ 70)

### Feedback geben

1. Öffne `match-analysis.md` in Obsidian
2. Füge im Abschnitt `## Dein Feedback` deine Kommentare hinzu (z.B. "Remote-First ist mir wichtiger als du denkst")
3. Kopiere den Feedback-Text
4. Führe aus:

```bash
python main.py --startup "n8n" --feedback "Dein Feedback hier"
```

Das System aktualisiert dein Profil (`profile.md`) und führt das Matching erneut durch.

### Workflow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       ↓
┌─────────────┐
│    Scout    │ → Sammelt Rohdaten (Web, Podcasts, etc.)
└──────┬──────┘
       ↓
┌─────────────┐
│  Profiler   │ → Extrahiert Kultur-Profil
└──────┬──────┘
       ↓
┌─────────────┐
│  Matchmaker │ → Bewertet Fit (0-100)
└──────┬──────┘
       ↓
   ┌───┴───┐
   │Fit≥70?│
   └───┬───┘
       ├── Ja ──→ ┌───────────────┐
       │          │Pitch Architect│ → Generiert Door-Opener
       │          └───────┬───────┘
       │                  ↓
       │               ┌─────┐
       └──────────────→│ END │
                      └─────┘
       
   └── Nein ──→ ┌───────────────────┐
                │Wait for Feedback  │ → Speichert State
                └─────────┬─────────┘
                          ↓
                    User gibt Feedback
                          ↓
                ┌───────────────────┐
                │ Profile Updater   │ → Aktualisiert profile.md
                └─────────┬─────────┘
                          ↓
                    ┌─────────────┐
                    │  Matchmaker │ → Erneutes Matching
                    └─────────────┘
```

## Obsidian-Ordnerstruktur

```
/startup-screening/
  /_templates/
    startup-template.md
    profile-template.md
  /startups/
    /{startup-name}/
      raw-data.md
      culture-profile.md
      match-analysis.md
      pitch-proposal.md
  /media/
    /podcasts/
      {startup-name}-transcripts.md
    /interviews/
      {startup-name}-interviews.md
  profile.md           # Deine evolving Präferenzen
  feedback-log.md      # Alle Feedback-Einträge
```

## Architektur

Das System basiert auf **LangGraph** und orchestriert 5 spezialisierte Agenten:

1. **Scout**: Datensammler (Web, Social Media, Podcasts)
2. **Profiler**: Kultur-Analyst (extrahiert Werte, Red/Green Flags)
3. **Matchmaker**: Bewertet Fit gegen dein Profil
4. **Pitch Architect**: Generiert Door-Opener-Projektvorschlag
5. **Profile Updater**: Lernt aus deinem Feedback

Jeder Agent ist eine Node im Graph, der State wird durch alle Nodes gereicht. Bedingte Kanten steuern den Flow basierend auf dem Fit-Score.

## Tech-Stack

- **Python 3.10+**
- **LangGraph**: Orchestrierung der Agenten (zustandsbehafteter Graph)
- **LangChain**: LLM-Calls, Tools, Prompts
- **OpenAI GPT-4o**: LLM-Backend
- **Tavily API**: Web Search
- **ChromaDB**: Vektordatenbank für RAG (optional)
- **Obsidian**: UI und Speicher (Markdown-Dateien)

## Lizenz

MIT