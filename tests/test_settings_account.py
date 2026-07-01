"""Einstellungen: CSRF-Token im Formular + Konto-Löschung mit Abhängigkeiten."""
import re
from datetime import date, datetime, timedelta

from FullStackProject import create_app, db
from FullStackProject.models import (
    User, Goal, Photo, Connection, Message, Checkin, Rating, Appointment,
)


def _csrf(html, name="csrf_token"):
    m = re.search(r'name="' + name + r'"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None


def _make_user(email, name="Partner"):
    u = User(email=email, name=name)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://example.com/a/{name}.png", is_primary=True))
    u.goals.append(Goal(goal_category="Sport", goal_text="laufen"))
    db.session.add(u)
    db.session.commit()
    return u


# ---------------------------------------------------------------------------
# Teil 1 — CSRF-Token & Speichern der Benachrichtigung
# ---------------------------------------------------------------------------

def test_settings_save_works_with_csrf_enabled():
    """Mit aktivem CSRF bindet das Formular das Token ein und Speichern liefert
    kein 400 mehr (das war die Ursache des Fehlers)."""
    app = create_app()  # CSRF standardmässig aktiv
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SECRET_KEY="t")
    with app.app_context():
        db.create_all()
        u = User(email="csrf@e.com", name="Csrf"); u.set_password("passwort123")
        db.session.add(u); db.session.commit()

    client = app.test_client()
    client.post("/login", data={
        "email": "csrf@e.com", "password": "passwort123",
        "csrf_token": _csrf(client.get("/login").data.decode()),
    })
    page = client.get("/settings").data.decode()
    assert 'name="csrf_token"' in page                      # Token wird gerendert
    resp = client.post("/settings", data={"csrf_token": _csrf(page)}, follow_redirects=True)
    assert resp.status_code == 200                           # kein 400 mehr


def test_settings_toggle_off_and_on(app, logged_in_client, test_user):
    """Boolean wird korrekt gespeichert — auch der 'aus'-Zustand (Feld fehlt im POST)."""
    # aus: Checkbox nicht mitgesendet
    logged_in_client.post("/settings", data={}, follow_redirects=True)
    with app.app_context():
        assert db.session.get(User, test_user).notify_email is False
    # an: Checkbox mitgesendet
    logged_in_client.post("/settings", data={"notify_email": "y"}, follow_redirects=True)
    with app.app_context():
        assert db.session.get(User, test_user).notify_email is True


# ---------------------------------------------------------------------------
# Teil 2 — Konto löschen
# ---------------------------------------------------------------------------

def test_delete_wrong_password_keeps_account(app, logged_in_client, test_user):
    resp = logged_in_client.post(
        "/account/delete", data={"password": "falsch"}, follow_redirects=True
    )
    assert "Passwort falsch" in resp.data.decode()
    with app.app_context():
        assert db.session.get(User, test_user) is not None


def test_delete_removes_account_and_all_dependents(app, logged_in_client, test_user):
    with app.app_context():
        partner = _make_user("pal@e.com", "Pal")
        conn = Connection(user1_id=test_user, user2_id=partner.id, status="active")
        db.session.add(conn)
        db.session.commit()
        db.session.add_all([
            Message(connection_id=conn.id, sender_id=test_user, text="hi"),
            Checkin(user_id=test_user, checkin_date=date.today()),
            Appointment(match_id=conn.id, proposed_by=test_user,
                        scheduled_at=datetime.now() + timedelta(days=2)),
            Rating(rater_id=partner.id, ratee_id=test_user, stars=5),
            Rating(rater_id=test_user, ratee_id=partner.id, stars=4),
        ])
        db.session.commit()
        partner_id, conn_id = partner.id, conn.id

    resp = logged_in_client.post(
        "/account/delete", data={"password": "passwort123"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert "Anmelden" in resp.data.decode()  # auf Login-Seite gelandet

    with app.app_context():
        assert db.session.get(User, test_user) is None          # Konto weg
        assert db.session.get(User, partner_id) is not None      # Partner bleibt
        assert db.session.get(Connection, conn_id) is None       # Partnerschaft weg
        assert Message.query.count() == 0                        # Nachrichten weg
        assert Appointment.query.count() == 0                    # Termine weg
        assert Checkin.query.filter_by(user_id=test_user).count() == 0
        assert Goal.query.filter_by(user_id=test_user).count() == 0
        assert Rating.query.count() == 0                         # Bewertungen weg


def test_delete_ends_session(app, logged_in_client, test_user):
    """Nach dem Löschen ist man ausgeloggt — geschützte Seiten leiten zum Login."""
    logged_in_client.post("/account/delete", data={"password": "passwort123"})
    resp = logged_in_client.get("/settings")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
