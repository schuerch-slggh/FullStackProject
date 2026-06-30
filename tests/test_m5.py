"""M5: 1:1-Chat & Check-in (FA-07, FA-08, NFA-03)."""
from datetime import date, timedelta

from FullStackProject import db
from FullStackProject.models import User, Goal, Photo, Connection, Message, Checkin


def _make_user(email, name="Test"):
    u = User(email=email, name=name)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://i.pravatar.cc/300?u={email}", is_primary=True))
    return u


# ---------------------------------------------------------------------------
# FA-07 — 1:1-Chat
# ---------------------------------------------------------------------------

def test_send_message_persists_and_appears(app, logged_in_client, test_user):
    """A sent message is stored and still visible after reloading (FA-07 AK1/AK2)."""
    with app.app_context():
        partner = _make_user("partner@e.com", name="Partner")
        db.session.add(partner)
        db.session.commit()
        conn = Connection(user1_id=test_user, user2_id=partner.id, status="active")
        db.session.add(conn)
        db.session.commit()
        conn_id = conn.id

    logged_in_client.post(f"/chat/{conn_id}", data={"text": "Hallo Partner!"}, follow_redirects=True)

    # Reload the chat → message persisted and rendered
    resp = logged_in_client.get(f"/chat/{conn_id}")
    assert resp.status_code == 200
    assert "Hallo Partner!" in resp.data.decode()

    with app.app_context():
        assert Message.query.filter_by(connection_id=conn_id).count() == 1


def test_outsider_cannot_read_chat(app, logged_in_client, test_user):
    """A user who is not part of the connection gets 403 (FA-07 AK3 / NFA-03)."""
    with app.app_context():
        a = _make_user("a@e.com")
        b = _make_user("b@e.com")
        db.session.add_all([a, b])
        db.session.commit()
        conn = Connection(user1_id=a.id, user2_id=b.id, status="active")
        db.session.add(conn)
        db.session.commit()
        conn_id = conn.id

    resp = logged_in_client.get(f"/chat/{conn_id}")
    assert resp.status_code == 403


def test_chat_locked_until_active(app, logged_in_client, test_user):
    """A merely requested connection has no chat yet (FA-06 AK2)."""
    with app.app_context():
        partner = _make_user("req@e.com")
        db.session.add(partner)
        db.session.commit()
        conn = Connection(user1_id=test_user, user2_id=partner.id, status="requested")
        db.session.add(conn)
        db.session.commit()
        conn_id = conn.id

    resp = logged_in_client.get(f"/chat/{conn_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# FA-08 — Check-in & streak
# ---------------------------------------------------------------------------

def test_checkin_increases_streak(app, logged_in_client, test_user):
    """POST /checkin stores a check-in for today and the streak reflects it (FA-08 AK1)."""
    with app.app_context():
        assert db.session.get(User, test_user).streak == 0

    resp = logged_in_client.post("/checkin", data={"goal": "", "note": ""}, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        user = db.session.get(User, test_user)
        assert Checkin.query.filter_by(user_id=test_user, checkin_date=date.today()).count() == 1
        assert user.streak == 1


def test_streak_resets_on_missed_day(app):
    """Consecutive days count; a gap resets the streak (FA-08 AK2)."""
    with app.app_context():
        user = _make_user("streak@e.com")
        db.session.add(user)
        db.session.commit()
        today = date.today()

        # Three consecutive days ending today → streak 3
        for d in (0, 1, 2):
            db.session.add(Checkin(user_id=user.id, checkin_date=today - timedelta(days=d)))
        db.session.commit()
        assert user.streak == 3

        # A run that ended three days ago is stale → streak 0
        stale = _make_user("stale@e.com")
        db.session.add(stale)
        db.session.commit()
        for d in (3, 4, 5):
            db.session.add(Checkin(user_id=stale.id, checkin_date=today - timedelta(days=d)))
        db.session.commit()
        assert stale.streak == 0
