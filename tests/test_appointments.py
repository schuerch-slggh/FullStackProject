"""Terminvereinbarung zwischen gematchten Partnern (Appointment).

Deckt Vorschlag, Zu-/Absage, Zugriffsschutz (nur Empfänger reagiert, nur
Partner beteiligt) und den Grindprogress-Abschnitt "Offene Termine" ab. Alle
Tests nutzen genau einen eingeloggten Nutzer (test_user); dessen Rolle
(Vorschlagender vs. Empfänger) wird über direkt angelegte Termine gesteuert.
"""
from datetime import date, datetime, timedelta

from FullStackProject import db
from FullStackProject.models import User, Goal, Photo, Connection, Appointment


def _make_user(email, name="Partner"):
    u = User(email=email, name=name)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://example.com/a/{name}.png", is_primary=True))
    u.goals.append(Goal(goal_category="Sport", goal_text="3x pro Woche laufen"))
    db.session.add(u)
    db.session.commit()
    return u


def _partner_conn(test_user, email="partner@e.com"):
    """Aktive Partnerschaft zwischen test_user und einem neuen Partner."""
    partner = _make_user(email)
    conn = Connection(user1_id=test_user, user2_id=partner.id, status="active")
    db.session.add(conn)
    db.session.commit()
    return partner.id, conn.id


def _add_appt(conn_id, proposed_by, *, days=3, status="vorgeschlagen"):
    appt = Appointment(
        match_id=conn_id, proposed_by=proposed_by, status=status,
        scheduled_at=datetime.now() + timedelta(days=days),
    )
    db.session.add(appt)
    db.session.commit()
    return appt.id


def _future(days=3):
    d = date.today() + timedelta(days=days)
    return d.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Vorschlagen
# ---------------------------------------------------------------------------

def test_propose_creates_open_appointment(app, logged_in_client, test_user):
    with app.app_context():
        _, conn_id = _partner_conn(test_user)

    resp = logged_in_client.post(
        "/appointment/propose",
        data={"conn_id": conn_id, "date": _future(), "time": "18:30"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        appt = Appointment.query.one()
        assert appt.status == "vorgeschlagen"
        assert appt.proposed_by == test_user


def test_propose_in_past_is_rejected(app, logged_in_client, test_user):
    with app.app_context():
        _, conn_id = _partner_conn(test_user)

    resp = logged_in_client.post(
        "/appointment/propose",
        data={"conn_id": conn_id, "date": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), "time": "10:00"},
        follow_redirects=True,
    )
    assert "Vergangenheit" in resp.data.decode()
    with app.app_context():
        assert Appointment.query.count() == 0


def test_propose_requires_membership(app, logged_in_client, test_user):
    """Ein Vorschlag an eine fremde Partnerschaft ist nicht erlaubt."""
    with app.app_context():
        a = _make_user("out1@e.com")
        b = _make_user("out2@e.com")
        conn = Connection(user1_id=a.id, user2_id=b.id, status="active")
        db.session.add(conn)
        db.session.commit()
        foreign_conn = conn.id

    resp = logged_in_client.post(
        "/appointment/propose",
        data={"conn_id": foreign_conn, "date": _future(), "time": "18:00"},
    )
    assert resp.status_code == 403
    with app.app_context():
        assert Appointment.query.count() == 0


# ---------------------------------------------------------------------------
# Reaktion im Chat: Sichtbarkeit & Zugriffsschutz
# ---------------------------------------------------------------------------

def test_recipient_sees_actions(app, logged_in_client, test_user):
    """Ist test_user der Empfänger, zeigt der Chat Zusagen/Ablehnen."""
    with app.app_context():
        partner_id, conn_id = _partner_conn(test_user)
        _add_appt(conn_id, proposed_by=partner_id)  # partner schlägt vor

    html = logged_in_client.get(f"/chat/{conn_id}").data.decode()
    assert "Terminvorschlag" in html
    assert "Zusagen" in html and "Ablehnen" in html


def test_proposer_sees_no_actions(app, logged_in_client, test_user):
    """Der Vorschlagende sieht keine Buttons, nur 'wartet auf Antwort'."""
    with app.app_context():
        _, conn_id = _partner_conn(test_user)
        _add_appt(conn_id, proposed_by=test_user)  # test_user schlägt vor

    html = logged_in_client.get(f"/chat/{conn_id}").data.decode()
    assert "wartet auf Antwort" in html
    assert "Zusagen" not in html


def test_recipient_can_confirm(app, logged_in_client, test_user):
    with app.app_context():
        partner_id, conn_id = _partner_conn(test_user)
        appt_id = _add_appt(conn_id, proposed_by=partner_id)

    resp = logged_in_client.post(f"/appointment/{appt_id}/confirm", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Appointment, appt_id).status == "bestätigt"


def test_recipient_can_decline(app, logged_in_client, test_user):
    with app.app_context():
        partner_id, conn_id = _partner_conn(test_user)
        appt_id = _add_appt(conn_id, proposed_by=partner_id)

    logged_in_client.post(f"/appointment/{appt_id}/decline", follow_redirects=True)
    with app.app_context():
        assert db.session.get(Appointment, appt_id).status == "abgelehnt"


def test_proposer_cannot_confirm_own(app, logged_in_client, test_user):
    """Nur der Empfänger darf reagieren — der Vorschlagende nicht (403)."""
    with app.app_context():
        _, conn_id = _partner_conn(test_user)
        appt_id = _add_appt(conn_id, proposed_by=test_user)

    resp = logged_in_client.post(f"/appointment/{appt_id}/confirm")
    assert resp.status_code == 403
    with app.app_context():
        assert db.session.get(Appointment, appt_id).status == "vorgeschlagen"


def test_stranger_cannot_confirm(app, logged_in_client, test_user):
    """Wer nicht Teil der Partnerschaft ist, kann nicht reagieren (403)."""
    with app.app_context():
        a = _make_user("s1@e.com")
        b = _make_user("s2@e.com")
        conn = Connection(user1_id=a.id, user2_id=b.id, status="active")
        db.session.add(conn)
        db.session.commit()
        appt_id = _add_appt(conn.id, proposed_by=a.id)

    resp = logged_in_client.post(f"/appointment/{appt_id}/confirm")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Grindprogress: "Offene Termine"
# ---------------------------------------------------------------------------

def test_grindprogress_lists_upcoming_only(app, logged_in_client, test_user):
    """Offene Vorschläge + bestätigte künftige erscheinen; Vergangenes/Abgelehntes nicht."""
    with app.app_context():
        partner_id, conn_id = _partner_conn(test_user, email="pp@e.com")
        # offener Vorschlag (test_user ist Empfänger) → Aktion sichtbar
        _add_appt(conn_id, proposed_by=partner_id, days=2, status="vorgeschlagen")
        # bestätigter künftiger Termin
        _add_appt(conn_id, proposed_by=test_user, days=5, status="bestätigt")
        # abgelehnt → versteckt
        _add_appt(conn_id, proposed_by=partner_id, days=4, status="abgelehnt")
        # vergangener bestätigter → versteckt
        past = Appointment(match_id=conn_id, proposed_by=test_user, status="bestätigt",
                           scheduled_at=datetime.now() - timedelta(days=1))
        db.session.add(past)
        db.session.commit()

    html = logged_in_client.get("/grindprogress").data.decode()
    assert "Offene Termine" in html
    assert "Offene Vorschläge" in html and "Zusagen" in html  # Empfänger-Aktion
    assert "bestätigt" in html
    # genau zwei Termin-Zeilen (offen + bestätigt); Vergangenes/Abgelehntes fehlt
    assert html.count('class="appt-row"') == 2
