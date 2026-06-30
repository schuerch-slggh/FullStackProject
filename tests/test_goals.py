"""Goal-Management: Commitments hinzufügen und löschen."""
from FullStackProject import db
from FullStackProject.models import User, Goal


def test_add_goal_redirects_anonymous(client):
    resp = client.get("/goals/new")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_add_goal_saves_new_goal(app, logged_in_client, test_user):
    resp = logged_in_client.post("/goals/new", data={
        "goal_category": "Lernen",
        "goal_text": "Python meistern",
        "frequency": "täglich",
        "preferred_checkin_time": "20:00",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        goals = Goal.query.filter_by(user_id=test_user).all()
        assert any(g.goal_text == "Python meistern" for g in goals)


def test_delete_own_goal(app, logged_in_client, test_user):
    with app.app_context():
        goal = Goal(user_id=test_user, goal_category="Projekt", goal_text="Zum Löschen")
        db.session.add(goal)
        db.session.commit()
        goal_id = goal.id

    resp = logged_in_client.post(f"/goals/{goal_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Goal, goal_id) is None


def test_delete_other_users_goal_forbidden(app, client, test_user):
    with app.app_context():
        other = User(
            email="other@example.com",
            name="Other User",
            photo_url="https://i.pravatar.cc/300?u=other@example.com",
        )
        other.set_password("passwort123")
        db.session.add(other)
        db.session.commit()
        goal = Goal(user_id=other.id, goal_category="Sport", goal_text="Anderes Ziel")
        db.session.add(goal)
        db.session.commit()
        goal_id = goal.id

    client.post("/login", data={"email": "test@example.com", "password": "passwort123"})
    resp = client.post(f"/goals/{goal_id}/delete")
    assert resp.status_code == 403
