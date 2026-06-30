"""M6: Sonderfunktionen — Erinnerungen (FA-09), E-Mail (FA-10), KI-Coach (FA-11/NFA-09)."""
from datetime import datetime, date

from FullStackProject import db, coach as coach_module
from FullStackProject.models import User, Goal, Photo, Connection, Checkin, due_reminders


def _make_user(email, name="Test", notify_email=True):
    u = User(email=email, name=name, notify_email=notify_email)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://i.pravatar.cc/300?u={email}", is_primary=True))
    return u


def _today_at(hour):
    return datetime.combine(date.today(), datetime.min.time()).replace(hour=hour)


# ---------------------------------------------------------------------------
# FA-09 — Check-in-Schedule / Erinnerungen
# ---------------------------------------------------------------------------

def test_reminder_due_when_time_passed(app):
    """Ein geplantes Ziel ohne heutigen Check-in ist nach der Uhrzeit fällig (FA-09 AK2)."""
    with app.app_context():
        u = _make_user("rem@e.com")
        u.goals.append(Goal(goal_category="Sport", goal_text="Laufen",
                            preferred_checkin_time="08:00"))
        db.session.add(u)
        db.session.commit()
        assert len(due_reminders(u, now=_today_at(9))) == 1
        # Vor der geplanten Zeit ist nichts fällig.
        assert due_reminders(u, now=_today_at(7)) == []


def test_reminder_cleared_after_checkin(app):
    """Nach einem Check-in für das Ziel ist die Erinnerung weg (FA-09)."""
    with app.app_context():
        u = _make_user("rem2@e.com")
        g = Goal(goal_category="Sport", goal_text="Laufen", preferred_checkin_time="08:00")
        u.goals.append(g)
        db.session.add(u)
        db.session.commit()
        db.session.add(Checkin(user_id=u.id, goal_id=g.id, checkin_date=date.today()))
        db.session.commit()
        assert due_reminders(u, now=_today_at(9)) == []


# ---------------------------------------------------------------------------
# FA-10 — E-Mail-Notification + Ein/Aus-Schalter
# ---------------------------------------------------------------------------

def _active_partner(app, test_user, email, notify_email):
    with app.app_context():
        partner = _make_user(email, name="Partner", notify_email=notify_email)
        db.session.add(partner)
        db.session.commit()
        conn = Connection(user1_id=test_user, user2_id=partner.id, status="active")
        db.session.add(conn)
        db.session.commit()
        return conn.id


def test_message_sends_email_to_partner(app, logged_in_client, test_user):
    """Eine neue Nachricht löst eine E-Mail an den Partner aus (FA-10 AK1)."""
    conn_id = _active_partner(app, test_user, "p@e.com", notify_email=True)
    app.config["EMAIL_OUTBOX"] = []
    logged_in_client.post(f"/chat/{conn_id}", data={"text": "Hallo!"}, follow_redirects=True)
    outbox = app.config["EMAIL_OUTBOX"]
    assert len(outbox) == 1
    assert outbox[0]["to"] == "p@e.com"


def test_no_email_when_partner_opted_out(app, logged_in_client, test_user):
    """Hat der Partner Benachrichtigungen aus, wird keine E-Mail versendet (FA-10 AK2)."""
    conn_id = _active_partner(app, test_user, "p2@e.com", notify_email=False)
    app.config["EMAIL_OUTBOX"] = []
    logged_in_client.post(f"/chat/{conn_id}", data={"text": "Hallo!"}, follow_redirects=True)
    assert app.config["EMAIL_OUTBOX"] == []


def test_settings_toggle_persists(app, logged_in_client, test_user):
    """Der Schalter in den Einstellungen wird gespeichert (FA-10 AK2)."""
    # Checkbox nicht gesetzt → deaktiviert.
    logged_in_client.post("/settings", data={}, follow_redirects=True)
    with app.app_context():
        assert db.session.get(User, test_user).notify_email is False


# ---------------------------------------------------------------------------
# FA-11 / NFA-09 — KI-Coach offline-Fallback und Datensparsamkeit
# ---------------------------------------------------------------------------

def test_sharpen_goal_offline_fallback(app, monkeypatch):
    """Ohne API-Key liefert sharpen_goal eine sinnvolle lokale Umformulierung (FA-11 AK2)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with app.app_context():
        out = coach_module.sharpen_goal("mehr Sport machen")
    assert out and "mehr Sport machen" in out


def test_coach_prompts_are_data_minimal(app):
    """Prompts enthalten nur Ziel/Streak — keine Zugangsdaten o.ä. (NFA-09 AK1)."""
    sharpen = coach_module.sharpen_prompt("mehr lesen")
    motivate = coach_module.motivation_prompt(5, "mehr lesen")
    assert "mehr lesen" in sharpen
    assert "5" in motivate
    for prompt in (sharpen, motivate):
        assert "passwort" not in prompt.lower()
        assert "@" not in prompt
