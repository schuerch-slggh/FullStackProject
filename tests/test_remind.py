"""Partner-Erinnerung per E-Mail auf der Grindprogress-Seite.

Deckt die Route POST /partner/<id>/remind ab: erfolgreicher Versand über den
bestehenden Mailer, Rate-Limit (1×/Tag), Blockade bei bereits erfolgtem
Check-in, Zugriffsschutz und Datenschutz (Partner-E-Mail nie im HTML).
"""
from datetime import date

from FullStackProject import db
from FullStackProject.models import User, Goal, Photo, Connection, Checkin


def _make_partner(email, name="Partner", notify=True, checked_in_today=False):
    u = User(email=email, name=name, notify_email=notify)
    u.set_password("passwort123")
    # Avatar-URL bewusst OHNE E-Mail, damit der HTML-Datenschutz-Test wirklich
    # prüft, dass unser Code die Adresse nicht ausgibt (nicht die Foto-URL).
    u.photos.append(Photo(url=f"https://example.com/a/{name}.png", is_primary=True))
    u.goals.append(Goal(goal_category="Sport", goal_text="3x pro Woche laufen"))
    db.session.add(u)
    db.session.commit()
    if checked_in_today:
        db.session.add(Checkin(user_id=u.id, checkin_date=date.today()))
        db.session.commit()
    return u


def _partner_with_connection(test_user, **kwargs):
    """Aktiver Partner des eingeloggten Test-Nutzers; gibt (id, email) zurück."""
    partner = _make_partner(**kwargs)
    db.session.add(Connection(user1_id=test_user, user2_id=partner.id, status="active"))
    db.session.commit()
    return partner.id, partner.email


def test_remind_sends_email_when_partner_open(app, logged_in_client, test_user):
    """Ein offener Partner-Check-in löst genau eine E-Mail an den Partner aus."""
    with app.app_context():
        pid, pemail = _partner_with_connection(test_user, email="open@e.com", name="Bob")

    resp = logged_in_client.post(f"/partner/{pid}/remind")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    outbox = app.config.get("EMAIL_OUTBOX", [])
    assert len(outbox) == 1
    assert outbox[0]["to"] == pemail
    assert "Test User" in outbox[0]["subject"]  # Name des erinnernden Nutzers


def test_remind_rate_limited_once_per_day(app, logged_in_client, test_user):
    """Eine zweite Erinnerung am selben Tag wird abgelehnt und sendet nichts."""
    with app.app_context():
        pid, _ = _partner_with_connection(test_user, email="twice@e.com")

    first = logged_in_client.post(f"/partner/{pid}/remind")
    assert first.get_json()["ok"] is True

    second = logged_in_client.post(f"/partner/{pid}/remind")
    assert second.status_code == 200
    body = second.get_json()
    assert body["ok"] is False
    assert "erinnert" in body["message"].lower()
    # Kein zweiter Versand
    assert len(app.config.get("EMAIL_OUTBOX", [])) == 1


def test_remind_blocked_when_partner_checked_in(app, logged_in_client, test_user):
    """Hat der Partner heute schon eingecheckt, wird nicht erinnert."""
    with app.app_context():
        pid, _ = _partner_with_connection(
            test_user, email="done@e.com", checked_in_today=True
        )

    resp = logged_in_client.post(f"/partner/{pid}/remind")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is False
    assert "eingecheckt" in resp.get_json()["message"].lower()
    assert app.config.get("EMAIL_OUTBOX", []) == []


def test_remind_requires_active_partnership(app, logged_in_client, test_user):
    """Ohne aktive Partnerschaft ist keine Erinnerung möglich (Zugriffsschutz)."""
    with app.app_context():
        stranger = _make_partner(email="stranger@e.com")
        sid = stranger.id

    resp = logged_in_client.post(f"/partner/{sid}/remind")
    assert resp.status_code == 403
    assert resp.get_json()["ok"] is False
    assert app.config.get("EMAIL_OUTBOX", []) == []


def test_remind_respects_partner_optout(app, logged_in_client, test_user):
    """Hat der Partner E-Mails deaktiviert, wird nichts gesendet."""
    with app.app_context():
        pid, _ = _partner_with_connection(test_user, email="optout@e.com", notify=False)

    resp = logged_in_client.post(f"/partner/{pid}/remind")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is False
    assert app.config.get("EMAIL_OUTBOX", []) == []


def test_partner_email_never_in_grindprogress_html(app, logged_in_client, test_user):
    """Die E-Mail-Adresse des Partners darf nie im gerenderten HTML stehen (NFA-03)."""
    with app.app_context():
        _partner_with_connection(test_user, email="secret@e.com", name="Carla")

    resp = logged_in_client.get("/grindprogress")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "Carla" in html            # Partner erscheint
    assert "secret@e.com" not in html  # aber nie dessen E-Mail
