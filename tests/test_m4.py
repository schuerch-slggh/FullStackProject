"""M4: Suche, Match-Algorithmus & Verbindung."""
import pytest

from FullStackProject import db
from FullStackProject.models import User, Goal, Photo, Connection, match_score


def _make_user(email, name="Test", city=None, goals=None):
    u = User(email=email, name=name, city=city)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://i.pravatar.cc/300?u={email}", is_primary=True))
    for g in (goals or []):
        u.goals.append(Goal(**g))
    return u


def _sport_goal(**kw):
    return dict(goal_category="Sport", goal_text="Laufen", frequency="täglich",
                preferred_checkin_time="08:00", **kw)


# ---------------------------------------------------------------------------
# match_score
# ---------------------------------------------------------------------------

def test_match_score_full_overlap(app):
    """Same category + frequency + time → score 4."""
    with app.app_context():
        u1 = _make_user("s1@e.com", goals=[_sport_goal()])
        u2 = _make_user("s2@e.com", goals=[_sport_goal()])
        db.session.add_all([u1, u2])
        db.session.commit()
        assert match_score(u1, u2) == 4


def test_match_score_category_only(app):
    """Same category, different frequency and time → score 2."""
    with app.app_context():
        u1 = _make_user("c1@e.com", goals=[_sport_goal()])
        u2 = _make_user("c2@e.com", goals=[
            dict(goal_category="Sport", goal_text="Schwimmen",
                 frequency="3x pro Woche", preferred_checkin_time="20:00")
        ])
        db.session.add_all([u1, u2])
        db.session.commit()
        assert match_score(u1, u2) == 2


def test_match_score_no_overlap(app):
    """Completely different goals → score 0."""
    with app.app_context():
        u1 = _make_user("n1@e.com", goals=[dict(goal_category="Sport", goal_text="X",
                                                  frequency="täglich", preferred_checkin_time="08:00")])
        u2 = _make_user("n2@e.com", goals=[dict(goal_category="Lernen", goal_text="Y",
                                                  frequency="3x pro Woche", preferred_checkin_time="20:00")])
        db.session.add_all([u1, u2])
        db.session.commit()
        assert match_score(u1, u2) == 0


# ---------------------------------------------------------------------------
# Connection.between
# ---------------------------------------------------------------------------

def test_connection_between_any_direction(app):
    """Connection.between finds a connection regardless of which user is user1."""
    with app.app_context():
        u1 = _make_user("b1@e.com")
        u2 = _make_user("b2@e.com")
        u3 = _make_user("b3@e.com")
        db.session.add_all([u1, u2, u3])
        db.session.commit()
        db.session.add(Connection(user1_id=u1.id, user2_id=u2.id, status="requested"))
        db.session.commit()
        assert Connection.between(u1.id, u2.id) is not None
        assert Connection.between(u2.id, u1.id) is not None
        assert Connection.between(u1.id, u3.id) is None


# ---------------------------------------------------------------------------
# Search route
# ---------------------------------------------------------------------------

def test_search_excludes_self(app, logged_in_client, test_user):
    """Current user never appears in their own search results."""
    # test_user has 'Sport' goal — searching Sport with no other users → empty results
    resp = logged_in_client.get("/search?category=Sport&frequency=&city=&submit=Suchen")
    assert resp.status_code == 200
    assert "Kein passender Partner" in resp.data.decode()


def test_search_category_filter(app, logged_in_client, test_user):
    """Category filter returns matching users and excludes non-matching ones."""
    with app.app_context():
        learner = _make_user("learner@e.com", name="Lern-Mensch", goals=[
            dict(goal_category="Lernen", goal_text="Bücher lesen",
                 frequency="täglich", preferred_checkin_time="21:00")
        ])
        db.session.add(learner)
        db.session.commit()

    resp = logged_in_client.get("/search?category=Lernen&frequency=&city=&submit=Suchen")
    data = resp.data.decode()
    assert resp.status_code == 200
    assert "Lern-Mensch" in data       # Learner appears
    assert "Test User" not in data     # test_user (Sport) excluded


# ---------------------------------------------------------------------------
# Connection flow
# ---------------------------------------------------------------------------

def test_send_connection_request(app, logged_in_client, test_user):
    """POST /connect/<id> creates a 'requested' connection in the database."""
    with app.app_context():
        other = _make_user("recv@e.com", name="Receiver")
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    resp = logged_in_client.post(f"/connect/{other_id}", follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        conn = Connection.query.filter_by(user2_id=other_id).first()
        assert conn is not None
        assert conn.status == "requested"


def test_accept_connection_changes_status(app, logged_in_client, test_user):
    """Receiver (logged-in test_user) accepts → status becomes 'active'."""
    with app.app_context():
        sender = _make_user("sender@e.com", name="Sender")
        db.session.add(sender)
        db.session.commit()
        conn = Connection(user1_id=sender.id, user2_id=test_user, status="requested")
        db.session.add(conn)
        db.session.commit()
        conn_id = conn.id

    resp = logged_in_client.post(f"/connections/{conn_id}/accept", follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        assert db.session.get(Connection, conn_id).status == "active"


def test_cannot_connect_to_self(app, logged_in_client, test_user):
    """POST /connect/<own_id> returns 400."""
    resp = logged_in_client.post(f"/connect/{test_user}")
    assert resp.status_code == 400
