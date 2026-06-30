# CLAUDE.md — Auto-Kontext für Claude Code

Diese Datei wird von Claude Code bei jeder Sitzung automatisch gelesen. Sie ist
der Einstieg; die ausführlichen Regeln und der Projektstand stehen in den
verlinkten Dateien.

## Session-Start (immer zuerst)

1. Lies `ClaudeCode.md` — die verbindlichen Ausführungs- und Engineering-Regeln.
2. Lies `PROJECT.md` — aktueller Stand, Meilenstein-Checkliste, nächster Schritt.
3. Lies `README.md` — wie man die App startet, testet und konfiguriert.

Bei Widersprüchen gilt die Priorität aus `ClaudeCode.md` (laufender Code und
Tests vor Doku). Arbeite strikt nach dem Meilenstein-Workflow in `ClaudeCode.md`.

## Worum es geht

Modul **Full Stack Web Development FS2026** (Wirtschaftsinformatik, letztes
Modul). Gruppenprojekt (2–3 Personen), Web-App **from scratch** in Python/Flask.
Idee: **Accountability-Partner** ("Momentum") — Menschen mit ähnlichen Zielen
finden sich und halten sich per Check-in gegenseitig auf Kurs.

Das Projekt umfasst Frontend, Backend und Datenbank/Datenmodell gleichermaßen;
arbeite am gesamten Stack, nicht nur an einer Rolle.

## Tech-Stack

- Flask mit `create_app()`-Factory in `__init__.py`, Einstieg über `main.py`
- Flask-SQLAlchemy (ORM/Entities), Flask-Login (Auth), Flask-WTF (Formulare, CSRF)
- Jinja2-Templates, Bootstrap 5 via CDN, eigene Identität in `static/style.css`
- DB: lokal SQLite (`instance/app.db`), final MySQL via `DATABASE_URL`
  (`mysql+pymysql://user:pass@localhost:3306/db`) — ohne Code-Änderung
- Passwort-Hashing mit `method="pbkdf2:sha256"`

## Architektur (Separation of Concerns)

- **Controller** = Blueprints (`auth.py`, `views.py`): validieren und delegieren,
  enthalten keine Kernlogik.
- **Entities** = `models.py` (SQLAlchemy).
- **Forms** = `forms.py` (Validierung an der Grenze, Flask-WTF).
- **Views/Darstellung** = `templates/` + `static/`.

## Anforderungen als Quelle der Wahrheit

Funktionsumfang, Prioritäten (MoSCoW) und Akzeptanzkriterien stehen im
**Anforderungskatalog** (`docs/anforderungskatalog.md`, FA-01…FA-16 /
NFA-01…NFA-09). Meilensteine in `PROJECT.md` referenzieren diese IDs. „Must" =
nötig für die 4.0; „Should/Could" = Ausbau Richtung 6.0.

## Befehle

- Starten:  `flask --app main run --debug`  → http://127.0.0.1:5000
- DB füllen: `flask --app main seed`  (10 Dummy-Profile)
- Demo-Login: `anna.keller@example.com` / `accountability`

## Konventionen & Guardrails

- Deutsche UI-Texte und deutsche Commit-Messages, Feature-Branches + PRs.
- Keine Secrets ins Git (`SECRET_KEY`, `ANTHROPIC_API_KEY`, Mail-Zugänge via Env).
- Datenschutz (NFA-03): Chat-Inhalte nur für die beiden Partner; geschützte
  Seiten nur mit Login erreichbar.
- Zielkategorien **breit** halten (Lernen/Projekt/Sport/Gewohnheit). **Kein**
  detailliertes Ernährungs-/Kalorien-/Gewichts-Tracking.
- Beim KI-Coach (NFA-09) nur nötige Daten an die externe Schnittstelle senden,
  keine fremden Chat-Inhalte, keine Zugangsdaten.

## Bewertung — worauf optimieren

4.0 = alle Grundfunktionen + 3 Sonderfunktionen + 3 Abgabe-Artefakte
(Git-Release, Video-Demo, Projekt-Tagebuch). Richtung 6.0 = exzellentes
UX-Design und Zusatzfunktionen; Front- **und** Backend werden bewertet.
