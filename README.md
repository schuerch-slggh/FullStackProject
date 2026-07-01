# GrindMate — Accountability-Partner-App

Web-App für das Modul Full Stack Web Development FS2026. Nutzer legen ein Zielprofil an, finden passende Partner und halten sich per Check-in gegenseitig auf Kurs.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## App starten

```bash
flask --app main run --debug
```

Öffne http://127.0.0.1:5000

## Datenbank befüllen (Demo-Daten)

```bash
flask --app main seed
```

Demo-Login: `anna.keller@example.com` / `accountability`

## Tests ausführen

```bash
pytest tests/ -v
```

## Konfiguration

Variablen lokal per `.env`-Datei setzen (wird automatisch via `python-dotenv`
geladen, liegt in `.gitignore` und wird nie committet):

```bash
cp .env.example .env
# .env bearbeiten und echte Werte eintragen
```

| Variable | Zweck | Standard |
|---|---|---|
| `SECRET_KEY` | Session-Sicherheit | `dev-secret-change-me` |
| `DATABASE_URL` | Datenbank-URI | SQLite `instance/app.db` |
| `MAIL_SERVER` | SMTP-Host für E-Mail-Notification (FA-10) | _leer → nur Log_ |
| `MAIL_PORT` | SMTP-Port | `587` |
| `MAIL_USE_TLS` | STARTTLS verwenden (`1`/`0`) | `1` |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | SMTP-Login | _leer_ |
| `MAIL_SENDER` | Absenderadresse | `noreply@grindmate.local` |
| `ANTHROPIC_API_KEY` | KI-Coach via Anthropic-API (FA-11) | _leer → lokaler Fallback_ |

MySQL-Beispiel: `DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/db`

Ohne `MAIL_SERVER` werden E-Mails nur geloggt; ohne `ANTHROPIC_API_KEY` nutzt der
KI-Coach eine deterministische lokale Formulierung. Beides hält die App ohne
externe Dienste lauffähig.

## Routen

| Route | Beschreibung |
|---|---|
| `/` | Startseite (Landing Page) |
| `/register` | Registrierung |
| `/login` / `/logout` | Authentifizierung |
| `/profile` | Eigenes Profil (Login erforderlich) |
| `/profile/edit` | Profil bearbeiten + Foto hochladen |
| `/goals/new` | Commitment hinzufügen |
| `/goals/<id>/delete` | Commitment löschen (POST) |
| `/u/<id>` | Fremdprofil ansehen |
| `/search` | Partner suchen + Match-Score (GET) |
| `/matches` | Top-3-Match-Vorschläge je eigenem Ziel, ohne Filter (GET) |
| `/connect/<id>` | Verbindungsanfrage senden (POST) |
| `/connections/<id>/accept` | Anfrage annehmen (POST) |
| `/connections/<id>/decline` | Anfrage ablehnen / zurückziehen (POST) |
| `/rate/<id>` | Aktiven Partner bewerten (1–5 ★) für den Reputations-Score (POST) |
| `/chat/<id>` | 1:1-Chat einer aktiven Verbindung (GET zeigt Verlauf + markiert gelesen, POST sendet) |
| `/checkin` | Check-in für heute markieren (POST) |
| `/settings` | E-Mail-Benachrichtigungen an/aus (GET/POST) |
| `/coach` | KI-Coach-Seite (GET) |
| `/coach/motivate` | Motivierende Rückmeldung erzeugen (POST) |
| `/coach/sharpen` | Vages Ziel konkreter formulieren (POST) |

## Projektstruktur

```
__init__.py      App-Factory (create_app, CSRFProtect, DB, Login, MAIL_*-Config)
main.py          Einstiegspunkt
auth.py          Blueprint: Login, Logout, Registrierung
views.py         Blueprint: Profil (Erinnerungen + Fortschritts-Diagramm), Bearbeiten,
                            Goal-Verwaltung, Fremdprofil, Suche (match_score, nach
                            Reputation sortiert), Matches (Top-3 je Ziel), Verbindungen
                            (send/accept/decline), Partner bewerten (rate), Chat
                            (Lese-Markierung), Check-in, Einstellungen, KI-Coach;
                            before_app_request setzt last_seen
models.py        SQLAlchemy-Entities (User, Goal, Photo, Connection, Message, Checkin,
                 Rating)
                 + Domain-Helfer: match_score(), top_matches_for_goal(), due_reminders(),
                   checkin_history(), Connection.between()/.active_for()/.involves()/
                   .partner_of(); berechnete Properties User.streak/.reputation/
                   .activity_level/.avg_rating/.is_online; Spalten User.notify_email/
                   .last_seen, Message.read_at
forms.py         WTForms: LoginForm, RegistrationForm, EditProfileForm, GoalForm,
                          SearchForm, MessageForm, CheckinForm, SettingsForm,
                          CoachGoalForm, RatingForm
mailer.py        E-Mail-Notification (FA-10): send_email()/notify(), SMTP optional
coach.py         KI-Coach (FA-11): sharpen_goal()/motivational_message() via
                 Anthropic-API mit lokalem Offline-Fallback; datensparsam (NFA-09)
seed.py          CLI: flask seed (10 Profile + Connections, Messages, Checkins)
conftest.py      sys.path-Fix damit pytest das App-Paket im Repo-Root findet
static/          style.css, Uploads (static/uploads/)
templates/       Jinja2-Templates (landing, login, register, profile, edit_profile,
                 goal_form, user_profile, search, matches, chat, settings, coach)
doc/             ER-Modell (diagramms.md), Anforderungskatalog, Personas
tests/           pytest-Tests (47 Tests: test_m2 + test_goals + test_m3 + test_m4
                 + test_m5 + test_m6 + test_m7 + test_matches)
```
