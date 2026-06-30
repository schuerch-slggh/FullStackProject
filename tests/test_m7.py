"""M7: UX-Politur & Zusatzfunktionen (FA-12, FA-13, FA-16, NFA-04)."""
from datetime import date, datetime, timedelta

from FullStackProject import db
from FullStackProject.models import (
    User, Goal, Photo, Connection, Message, Checkin, Rating, checkin_history,
)


def _make_user(email, name="Test"):
    u = User(email=email, name=name)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://i.pravatar.cc/300?u={email}", is_primary=True))
    return u


def _active_partner(app, test_user, email):
    """Create a partner with an active connection to test_user; return (id, conn_id)."""
    with app.app_context():
        partner = _make_user(email, name="Partner")
        db.session.add(partner)
        db.session.commit()
        conn = Connection(user1_id=test_user, user2_id=partner.id, status="active")
        db.session.add(conn)
        db.session.commit()
        return partner.id, conn.id


# ---------------------------------------------------------------------------
# FA-12 — Streak- und Fortschrittsanzeige
# ---------------------------------------------------------------------------

def test_checkin_history_counts_per_day(app):
    """checkin_history returns one chronological entry per day with counts (FA-12 AK2)."""
    with app.app_context():
        u = _make_user("hist@e.com")
        db.session.add(u)
        db.session.commit()
        today = date.today()
        db.session.add_all([
            Checkin(user_id=u.id, checkin_date=today),
            Checkin(user_id=u.id, checkin_date=today),          # two on the same day
            Checkin(user_id=u.id, checkin_date=today - timedelta(days=3)),
        ])
        db.session.commit()

        hist = checkin_history(u, days=14, today=today)
        assert len(hist) == 14
        assert hist[-1] == {"date": today, "count": 2}          # newest last
        assert hist[0]["date"] == today - timedelta(days=13)    # oldest first
        assert next(h["count"] for h in hist if h["date"] == today - timedelta(days=3)) == 1


# ---------------------------------------------------------------------------
# FA-13 — Reputations-/Verlässlichkeits-Score
# ---------------------------------------------------------------------------

def test_activity_drives_reputation(app):
    """A user who checks in more has a higher reputation (FA-13 AK1)."""
    with app.app_context():
        active = _make_user("active@e.com")
        lazy = _make_user("lazy@e.com")
        db.session.add_all([active, lazy])
        db.session.commit()
        today = date.today()
        for d in range(14):                                     # checked in every day
            db.session.add(Checkin(user_id=active.id, checkin_date=today - timedelta(days=d)))
        db.session.commit()

        assert active.reputation > lazy.reputation
        assert active.reputation == 5.0                         # full activity, no ratings


def test_partner_rating_influences_score(app, logged_in_client, test_user):
    """An active partner's rating is stored and feeds the ratee's score (FA-13 AK2)."""
    partner_id, _ = _active_partner(app, test_user, "rate@e.com")

    resp = logged_in_client.post(f"/rate/{partner_id}", data={"stars": "5"}, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        partner = db.session.get(User, partner_id)
        assert Rating.query.filter_by(rater_id=test_user, ratee_id=partner_id).count() == 1
        assert partner.avg_rating == 5.0
        # No activity but a 5-star rating → reputation lifted above bare activity (0).
        assert partner.reputation == 2.5


def test_rerating_overwrites(app, logged_in_client, test_user):
    """Re-rating the same partner updates rather than duplicates (FA-13 AK2)."""
    partner_id, _ = _active_partner(app, test_user, "rate2@e.com")
    logged_in_client.post(f"/rate/{partner_id}", data={"stars": "5"}, follow_redirects=True)
    logged_in_client.post(f"/rate/{partner_id}", data={"stars": "2"}, follow_redirects=True)

    with app.app_context():
        ratings = Rating.query.filter_by(rater_id=test_user, ratee_id=partner_id).all()
        assert len(ratings) == 1
        assert ratings[0].stars == 2


def test_cannot_rate_without_active_connection(app, logged_in_client, test_user):
    """Rating a non-partner is forbidden (FA-13 AK2 / NFA-03)."""
    with app.app_context():
        stranger = _make_user("stranger@e.com")
        db.session.add(stranger)
        db.session.commit()
        stranger_id = stranger.id

    resp = logged_in_client.post(f"/rate/{stranger_id}", data={"stars": "5"})
    assert resp.status_code == 403
    with app.app_context():
        assert Rating.query.count() == 0


# ---------------------------------------------------------------------------
# FA-16 — Gesendet-/Gelesen- und Online-Status
# ---------------------------------------------------------------------------

def test_opening_chat_marks_partner_messages_read(app, logged_in_client, test_user):
    """Opening the chat marks the partner's messages as read (FA-16 AK1)."""
    partner_id, conn_id = _active_partner(app, test_user, "read@e.com")
    with app.app_context():
        db.session.add(Message(connection_id=conn_id, sender_id=partner_id, text="Hi!"))
        db.session.commit()
        assert Message.query.filter_by(connection_id=conn_id).first().read_at is None

    logged_in_client.get(f"/chat/{conn_id}")

    with app.app_context():
        msg = Message.query.filter_by(connection_id=conn_id).first()
        assert msg.read_at is not None


def test_is_online_reflects_last_seen(app):
    """is_online is true only within the activity window (FA-16 AK2)."""
    with app.app_context():
        u = _make_user("online@e.com")
        db.session.add(u)
        db.session.commit()
        assert u.is_online is False                             # never seen
        u.last_seen = datetime.utcnow()
        assert u.is_online is True
        u.last_seen = datetime.utcnow() - timedelta(minutes=10)
        assert u.is_online is False


# ---------------------------------------------------------------------------
# NFA-04 — Usability: Fehleingaben am Feld erklärt
# ---------------------------------------------------------------------------

def test_login_shows_field_error(app, client):
    """An empty login field is explained inline at the field (NFA-04 AK2)."""
    resp = client.post("/login", data={"email": "", "password": ""})
    assert resp.status_code == 200
    assert "field-error" in resp.data.decode()
