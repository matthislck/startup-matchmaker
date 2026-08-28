# Agent-Reach Setup Guide

Dieses Projekt nutzt `agent-reach` für tiefgehendes, kostenloses Multi-Platform-Scraping (LinkedIn, Twitter, Reddit, GitHub, YouTube).

## 1. Installation

Installiere das Paket via pip:

```bash
pip install agent-reach
```

Falls du Probleme hast, folge der [offiziellen Installationsanleitung](https://github.com/your-org/agent-reach).

## 2. Diagnose

Prüfe ob die Installation erfolgreich war:

```bash
agent-reach doctor
```

Dies sollte den Status aller Module und Abhängigkeiten anzeigen.

## 3. Konfiguration (Wichtig!)

`agent-reach` benötigt für bestimmte Plattformen (insbesondere LinkedIn und Twitter) authentifizierte Sessions, um Rate-Limits zu umgehen und private Daten zu sehen.

### LinkedIn Setup
```bash
agent-reach configure linkedin
```
Dies öffnet einen Browser-Login. Logge dich ein. Das Cookie wird lokal gespeichert.

### Twitter / X Setup
```bash
agent-reach configure twitter
```

### Sicherheitshinweis
⚠️ **Nutze für das Scraping idealerweise einen separaten Account**, nicht deinen primären privaten Business-Account. Aggressives Scraping kann zu temporären Sperren oder Rate-Limits führen. Ein "Burner-Account" minimiert das Risiko für dein Hauptprofil.

## 4. Nutzung im Projekt

Das System ruft `agent-reach` automatisch im Hintergrund auf. Stelle sicher, dass sich das Tool im `PATH` befindet.

Fehler beim Scraping werden in den Logs (`stdout`) und in der `raw-data.md` Datei im Obsidian Vault dokumentiert.

## 5. DACH-spezifische Quellen

Der Scout-Agent nutzt folgende DACH-optimierte Quellen:
- **Impressum-Suche**: Goldstandard für deutsche Firmen (Geschäftsführer-Namen)
- **Kununu**: Deutsche Arbeitgeber-Bewertungsplattform für Kultur-Signale
- **Gründerszene.de**: Führende deutsche Startup-News-Seite
- **Deutsche-Startups.de**: Weitere wichtige deutsche Startup-Quelle
- **OMR.com**: Online Marketing Rockstars – Interviews mit deutschen Gründern
- **Handelsblatt.com**: Wirtschaftszeitung für etablierte Unternehmen

## 6. Troubleshooting

### "Command not found"
Stelle sicher, dass `agent-reach` im PATH ist:
```bash
which agent-reach
```

### "Rate Limit exceeded"
- Warte einige Minuten zwischen den Scraping-Vorgängen
- Nutze authentifizierte Accounts (siehe Konfiguration)
- Erwäge die Nutzung eines VPNs für häufige Anfragen

### "Keine Gründer gefunden"
- Nutze das `--founder` Flag für manuelle Angabe:
```bash
python main.py --startup "n8n" --founder "Jan Oberhauser,David Fankhauser"
```
- Prüfe die Impressum-Seite des Startups manuell
