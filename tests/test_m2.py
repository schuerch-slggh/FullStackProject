"""M2: Profil bearbeiten, Foto-Upload, Fremdprofil-Ansicht."""
from FullStackProject import db
from FullStackProject.models import User


def test_edit_profile_redirects_anonymous(client):
    resp = client.get("/profile/edit")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_edit_profile_saves_changes(app, logged_in_client, test_user):
    resp = logged_in_client.post("/profile/edit", data={
        "name": "Neuer Name",
        "goal_category": "Lernen",
        "goal_text": "Python meistern",
        "age": "28",
        "city": "Zürich",
        "frequency": "5x pro Woche",
        "preferred_checkin_time": "19:00",
        "bio": "Motiviert dabei.",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        user = db.session.get(User, test_user)
        assert user.name == "Neuer Name"
        assert user.city == "Zürich"
        assert user.goal_text == "Python meistern"


def test_user_profile_shows_correct_user(app, logged_in_client, test_user):
    resp = logged_in_client.get(f"/u/{test_user}")
    assert resp.status_code == 200
    assert b"Test User" in resp.data


def test_user_profile_404_for_unknown_id(logged_in_client):
    resp = logged_in_client.get("/u/99999")
    assert resp.status_code == 404
