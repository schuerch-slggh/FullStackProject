"""Matches-Tab: Top-3-Vorschläge je eigenem Ziel (FA-05, pro Goal statt global)."""
from FullStackProject import db
from FullStackProject.models import User, Goal, Photo, top_matches_for_goal


def _make_user(email, name="Test", goals=None):
    u = User(email=email, name=name)
    u.set_password("passwort123")
    u.photos.append(Photo(url=f"https://i.pravatar.cc/300?u={email}", is_primary=True))
    for g in (goals or []):
        u.goals.append(Goal(**g))
    return u


def _sport_goal(**kw):
    base = dict(goal_category="Sport", goal_text="Laufen", frequency="täglich",
                preferred_checkin_time="08:00")
    base.update(kw)
    return base


def test_top_matches_excludes_self_and_other_categories(app):
    """Only users with a goal in the same category are candidates, never the owner."""
    with app.app_context():
        owner = _make_user("owner@e.com", goals=[_sport_goal()])
        same_cat = _make_user("same@e.com", goals=[_sport_goal(goal_text="Schwimmen")])
        other_cat = _make_user("other@e.com", goals=[
            dict(goal_category="Lernen", goal_text="Buch", frequency="täglich",
                 preferred_checkin_time="08:00")
        ])
        db.session.add_all([owner, same_cat, other_cat])
        db.session.commit()

        results = top_matches_for_goal(owner.goals[0])
        result_ids = {u.id for u, _ in results}
        assert same_cat.id in result_ids
        assert other_cat.id not in result_ids
        assert owner.id not in result_ids


def test_top_matches_ranks_full_overlap_first(app):
    """A candidate sharing category+frequency+time outranks a category-only match."""
    with app.app_context():
        owner = _make_user("owner2@e.com", goals=[_sport_goal()])
        full = _make_user("full@e.com", goals=[_sport_goal(goal_text="Joggen")])
        partial = _make_user("partial@e.com", goals=[
            dict(goal_category="Sport", goal_text="Yoga",
                 frequency="3x pro Woche", preferred_checkin_time="20:00")
        ])
        db.session.add_all([owner, full, partial])
        db.session.commit()

        results = top_matches_for_goal(owner.goals[0])
        assert [u.id for u, _ in results] == [full.id, partial.id]
        assert dict((u.id, s) for u, s in results) == {full.id: 4, partial.id: 2}


def test_top_matches_limit(app):
    """Only the best `limit` candidates are returned."""
    with app.app_context():
        owner = _make_user("owner3@e.com", goals=[_sport_goal()])
        others = [_make_user(f"c{i}@e.com", goals=[_sport_goal(goal_text=f"Ziel {i}")]) for i in range(5)]
        db.session.add_all([owner, *others])
        db.session.commit()

        assert len(top_matches_for_goal(owner.goals[0], limit=3)) == 3


def test_matches_route_groups_by_goal(app, logged_in_client, test_user):
    """GET /matches renders a section per own goal (test_user has one Sport goal)."""
    with app.app_context():
        candidate = _make_user("cand@e.com", name="Sport-Buddy", goals=[_sport_goal()])
        db.session.add(candidate)
        db.session.commit()

    resp = logged_in_client.get("/matches")
    data = resp.data.decode()
    assert resp.status_code == 200
    assert "Sport-Buddy" in data


def test_matches_route_requires_login(app, client):
    resp = client.get("/matches")
    assert resp.status_code == 302
