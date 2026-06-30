# Momentum — Accountability-Partner-App

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

| Variable | Zweck | Standard |
|---|---|---|
| `SECRET_KEY` | Session-Sicherheit | `dev-secret-change-me` |
| `DATABASE_URL` | Datenbank-URI | SQLite `instance/app.db` |

MySQL-Beispiel: `DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/db`

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
| `/connect/<id>` | Verbindungsanfrage senden (POST) |
| `/connections/<id>/accept` | Anfrage annehmen (POST) |
| `/connections/<id>/decline` | Anfrage ablehnen / zurückziehen (POST) |
| `/chat/<id>` | 1:1-Chat einer aktiven Verbindung (GET zeigt Verlauf, POST sendet) |
| `/checkin` | Check-in für heute markieren (POST) |

## Projektstruktur

```
__init__.py      App-Factory (create_app, CSRFProtect, DB, Login)
main.py          Einstiegspunkt
auth.py          Blueprint: Login, Logout, Registrierung
views.py         Blueprint: Profil, Bearbeiten, Goal-Verwaltung, Fremdprofil,
                            Suche (match_score), Verbindungen (send/accept/decline),
                            Chat (chat) und Check-in (checkin)
models.py        SQLAlchemy-Entities (User, Goal, Photo, Connection, Message, Checkin)
                 + Domain-Helfer: match_score(), Connection.between()/.active_for()/
                   .involves()/.partner_of(); berechnete Property User.streak
forms.py         WTForms: LoginForm, RegistrationForm, EditProfileForm,
                          GoalForm, SearchForm, MessageForm, CheckinForm
seed.py          CLI: flask seed (10 Profile + Connections, Messages, Checkins)
conftest.py      sys.path-Fix damit pytest das App-Paket im Repo-Root findet
static/          style.css, Uploads (static/uploads/)
templates/       Jinja2-Templates (landing, login, register, profile, edit_profile,
                 goal_form, user_profile, search, chat)
doc/             ER-Modell (diagramms.md), Anforderungskatalog, Personas
tests/           pytest-Tests (27 Tests: test_m2 + test_goals + test_m3 + test_m4 + test_m5)
```
