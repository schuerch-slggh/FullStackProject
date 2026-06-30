import pytest
from FullStackProject import create_app, db as _db
from FullStackProject.models import User, Goal, Photo


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret",
    )
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def test_user(app):
    with app.app_context():
        user = User(email="test@example.com", name="Test User")
        user.set_password("passwort123")
        user.photos.append(Photo(url="https://i.pravatar.cc/300?u=test@example.com", is_primary=True))
        user.goals.append(Goal(goal_category="Sport", goal_text="Jeden Tag laufen"))
        _db.session.add(user)
        _db.session.commit()
        return user.id


@pytest.fixture()
def logged_in_client(client, test_user):
    client.post("/login", data={"email": "test@example.com", "password": "passwort123"})
    return client
