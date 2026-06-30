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

## Routen (Stand M2)

| Route | Beschreibung |
|---|---|
| `/` | Startseite (Landing Page) |
| `/register` | Registrierung |
| `/login` / `/logout` | Authentifizierung |
| `/profile` | Eigenes Profil (Login erforderlich) |
| `/profile/edit` | Profil bearbeiten + Foto hochladen |
| `/u/<id>` | Fremdprofil ansehen |

## Projektstruktur

```
__init__.py      App-Factory (create_app)
main.py          Einstiegspunkt
auth.py          Blueprint: Login, Logout, Registrierung
views.py         Blueprint: Profil, Bearbeiten, Fremdprofil
models.py        SQLAlchemy-Entities (User)
forms.py         WTForms (Login, Registrierung, Profil bearbeiten)
seed.py          CLI: flask seed
static/          CSS, Uploads (static/uploads/)
templates/       Jinja2-Templates
tests/           pytest-Tests
```
