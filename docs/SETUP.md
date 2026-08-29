# Setup Guide - DACH Startup Matchmaker System

## Voraussetzungen

- Python 3.10+
- Obsidian (als UI/Storage)
- API Keys (siehe unten)

## Installation

### 1. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2. Umgebungsvariablen konfigurieren

Erstelle eine `.env` Datei im Projektverzeichnis:

```bash
cp .env.example .env
```

Bearbeite `.env` und füge deine API Keys ein:

```bash
OPENAI_API_KEY=sk-your-openai-key-here
TAVILY_API_KEY=tvly-your-tavily-key-here
GITHUB_TOKEN=ghp_your-github-token-optional  # Für höhere Rate Limits
OBSIDIAN_VAULT_PATH=/Users/dein-name/Obsidian Vault  # Pfad zu deinem Vault
```

#### API Keys besorgen:

1. **OpenAI API Key**: https://platform.openai.com/api-keys
   - Wird für LLM-Calls (GPT-4o empfohlen)
   - Kosten: ~$0.01-0.03 pro Startup-Analyse

2. **Tavily API Key**: https://app.tavily.com/
   - Kostenlose Tier verfügbar (1000 Suchanfragen/Monat)
   - Wird für Websuche verwendet

3. **GitHub Token** (optional): https://github.com/settings/tokens
   - Erhöht Rate Limits für GitHub API
   - Nicht zwingend erforderlich

### 3. Obsidian Vault vorbereiten

Das System erstellt automatisch folgende Struktur in deinem Vault:

```
/Obsidian Vault/
  /startup-screening/
    /startups/
      /{startup-name}/
        raw-data.md
        culture-profile.md
        match-analysis.md
        pitch-proposal.md
    profile.md
    feedback-log.md
```

Stelle sicher, dass der Pfad in `OBSIDIAN_VAULT_PATH` existiert.

## Usage

### Erstmaliges Screening

```bash
python main.py --startup "n8n"
```

Das System:
1. Scraped alle verfügbaren Daten (Website, News, Kununu, YouTube, GitHub, etc.)
2. Analysiert die Kultur des Startups
3. Vergleicht mit deinem Profil (profile.md)
4. Generiert Fit-Score und Begründung
5. Bei Score ≥ 70: Erstellt Pitch-Vorschlag

Alle Ergebnisse findest du in Obsidian unter `/startup-screening/startups/{startup-name}/`.

### Mit Founder-Override

Falls die automatische Gründer-Erkennung falsch liegt:

```bash
python main.py --startup "n8n" --founder "Jan Oberhauser,David Fankhauser"
```

### Feedback geben und System lernen lassen

1. Öffne `match-analysis.md` in Obsidian
2. Lies die Begründung des Fit-Scores
3. Füge im Abschnitt `## User Feedback` deine Kommentare hinzu
4. Kopiere dein Feedback
5. Führe aus:

```bash
python main.py --startup "n8n" --feedback "Remote-First ist mir wichtiger als gedacht. 'Work hard play hard' wäre ein Dealbreaker."
```

Das System:
- Aktualisiert dein Profil (profile.md)
- Führt Matching erneut durch
- Lernt aus deinem Feedback für zukünftige Analysen

## Troubleshooting

### "TAVILY_API_KEY not set"

Stelle sicher, dass:
1. `.env` Datei existiert
2. `TAVILY_API_KEY` korrekt gesetzt ist
3. Du `load_dotenv()` im Code aufrufst (bereits vorhanden)

### "OBSIDIAN_VAULT_PATH not found"

- Prüfe ob der Pfad in `.env` korrekt ist
- Verwende absolute Pfade (nicht relative)
- Beispiel macOS: `/Users/name/Obsidian Vault`
- Beispiel Windows: `C:/Users/name/Documents/Obsidian Vault`

### Scraping liefert keine Ergebnisse

Mögliche Ursachen:
1. Startup ist zu klein/unbekannt
2. API Key Limit erreicht (Tavily Free Tier: 1000/Monat)
3. Internetverbindung unterbrochen

Lösung:
- Prüfe `.env` auf korrekte API Keys
- Versuche bekannteres Startup zum Testen
- Prüfe Logs auf spezifische Fehlermeldungen

### YouTube Transkripte fehlen

Nicht alle Videos haben Untertitel. Das System:
- Versucht deutsche Transkripte优先
- Fällt auf englische zurück
- Markiert fehlende Transkripte klar in der Ausgabe

## Kostenübersicht

| API | Free Tier | Paid ab | Nutzung pro Startup |
|-----|-----------|---------|---------------------|
| OpenAI | $0 (Trial) | ~$0.03/call | 4-5 Calls (~$0.15) |
| Tavily | 1000/Monat | $29/Monat | ~10-15 Suchanfragen |
| GitHub | 5000/h | Kostenlos | 1-2 Calls |
| YouTube Transcript | Kostenlos | - | 2-3 Transkripte |

**Geschätzte Kosten pro Startup-Analyse: ~$0.15-0.20**

## Nächste Schritte

Nach erfolgreicher Installation:

1. Teste mit einem bekannten Startup: `python main.py --startup "personio"`
2. Öffne die generierten Dateien in Obsidian
3. Passe dein Profil in `profile.md` an deine Präferenzen an
4. Gib Feedback nach dem ersten Durchlauf
5. Wiederhole mit weiteren Startups

Bei Fragen oder Issues: Logs prüfen (`stdout`) und Fehlermeldungen analysieren.
