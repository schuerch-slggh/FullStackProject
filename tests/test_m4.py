"""M4: Suche, Match-Algorithmus & Verbindung."""
import pytest

from FullStackProject import db
from FullStackProject.models import (
    User, Goal, Photo, Connection,
    match_score, freq_to_per_week, rhythm_fit, time_to_min, time_fit,
)


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
# Matching v2a: normalization helpers (freq/time closeness instead of equality)
# ---------------------------------------------------------------------------

def test_freq_to_per_week_parses_known_patterns():
    assert freq_to_per_week("täglich") == 7.0
    assert freq_to_per_week("3x pro Woche") == 3.0
    assert freq_to_per_week("2x pro Monat") == pytest.approx(2 / 4.33)
    assert freq_to_per_week(None) is None
    assert freq_to_per_week("wann ich Lust habe") is None


def test_rhythm_fit_rewards_closeness_not_just_equality():
    """3x/4x pro Woche are 'close' now — the old exact-match gap this replaces."""
    assert rhythm_fit("täglich", "täglich") == 1.0
    assert rhythm_fit("3x pro Woche", "4x pro Woche") == pytest.approx(1 - 1 / 7)
    assert rhythm_fit("täglich", None) == 0.0


def test_time_fit_closeness_and_midnight_wrap():
    assert time_to_min("08:00") == 480
    assert time_to_min(None) is None
    assert time_fit("08:00", "08:30") == pytest.approx(1 - 30 / 180)
    assert time_fit("23:45", "00:15") == pytest.approx(1 - 30 / 180)  # wraps across midnight
    assert time_fit("08:00", None) == 0.0


# ---------------------------------------------------------------------------
# match_score
# ---------------------------------------------------------------------------

def test_match_score_ranks_by_overlap(app):
    """Full goal overlap outranks category-only overlap, which outranks none.

    v2a replaces the old 0–4 integer score with a continuous [0,1] weighted
    sum (domain/rhythm/timefit/reliab/intensity). For two fresh, single-goal,
    never-checked-in users reliab=0.34 and intensity=1.0 in every case here,
    so full overlap (domain=rhythm=timefit=1.0) comes out to a fixed
    (.30+.20+.15+.15*.34+.10)/.90 = 0.89.
    """
    with app.app_context():
        owner = _make_user("o1@e.com", goals=[_sport_goal()])
        full = _make_user("f1@e.com", goals=[_sport_goal()])
        partial = _make_user("p1@e.com", goals=[
            dict(goal_category="Sport", goal_text="Schwimmen",
                 frequency="3x pro Woche", preferred_checkin_time="20:00")
        ])
        none = _make_user("n1@e.com", goals=[
            dict(goal_category="Lernen", goal_text="Y",
                 frequency="3x pro Woche", preferred_checkin_time="20:00")
        ])
        db.session.add_all([owner, full, partial, none])
        db.session.commit()

        score_full = match_score(owner, full)
        score_partial = match_score(owner, partial)
        score_none = match_score(owner, none)

        assert score_full == pytest.approx(0.89)
        assert 0.0 <= score_none < score_partial < score_full <= 1.0


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
