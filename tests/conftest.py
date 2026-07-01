import os

import pytest

# Tests laufen IMMER gegen eine flüchtige In-Memory-SQLite — unabhängig von
# einer in .env gesetzten (Remote-/MySQL-)DATABASE_URL. `create_app()` liest
# DATABASE_URL beim Erstellen und ruft direkt `db.create_all()` auf; deshalb muss
# die Überschreibung HIER geschehen (nach dem Import, der .env via load_dotenv
# lädt, aber vor dem ersten create_app()-Aufruf in den Fixtures). Sonst würde
# sich jede der vielen Test-Apps mit der echten DB verbinden und z.B. deren
# Verbindungslimit sprengen.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

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
