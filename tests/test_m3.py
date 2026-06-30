"""M3: Vollständiges Datenmodell — Photo, Connection, Message, Checkin."""
from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from FullStackProject import db
from FullStackProject.models import User, Goal, Photo, Connection, Message, Checkin


def _make_user(email, name="Test"):
    u = User(email=email, name=name)
    u.set_password("passwort123")
    return u


def test_photo_url_property(app):
    """user.photo_url returns the primary photo's URL; column photo_url is gone."""
    with app.app_context():
        user = _make_user("photo@example.com")
        db.session.add(user)
        db.session.commit()

        # No photo yet → None
        assert user.photo_url is None

        user.photos.append(Photo(url="https://example.com/a.jpg", is_primary=False))
        db.session.commit()

        # Only non-primary → fallback to last photo
        assert user.photo_url == "https://example.com/a.jpg"

        user.photos.append(Photo(url="https://example.com/b.jpg", is_primary=True))
        db.session.commit()

        # Primary takes precedence
        assert user.photo_url == "https://example.com/b.jpg"

        # Confirm there is no photo_url column on the User table
        from sqlalchemy import inspect as sa_inspect
        cols = [c.name for c in sa_inspect(User).columns]
        assert "photo_url" not in cols


def test_connection_status_transition(app):
    """Connection starts as 'requested', transitions to 'active'."""
    with app.app_context():
        u1 = _make_user("u1@example.com")
        u2 = _make_user("u2@example.com")
        db.session.add_all([u1, u2])
        db.session.flush()

        conn = Connection(user1_id=u1.id, user2_id=u2.id, status="requested")
        db.session.add(conn)
        db.session.commit()

        assert conn.status == "requested"

        conn.status = "active"
        db.session.commit()

        refreshed = db.session.get(Connection, conn.id)
        assert refreshed.status == "active"
        assert refreshed.user1_id == u1.id
        assert refreshed.user2_id == u2.id


def test_message_linked_to_connection(app):
    """Message is retrievable via connection.messages and has correct sender."""
    with app.app_context():
        u1 = _make_user("msg1@example.com")
        u2 = _make_user("msg2@example.com")
        db.session.add_all([u1, u2])
        db.session.flush()

        conn = Connection(user1_id=u1.id, user2_id=u2.id, status="active")
        db.session.add(conn)
        db.session.flush()

        msg = Message(connection_id=conn.id, sender_id=u1.id, text="Hallo!")
        db.session.add(msg)
        db.session.commit()

        refreshed = db.session.get(Connection, conn.id)
        assert len(refreshed.messages) == 1
        assert refreshed.messages[0].text == "Hallo!"
        assert refreshed.messages[0].sender_id == u1.id


def test_checkin_query_by_user_and_date(app):
    """Checkin can be retrieved by user_id and checkin_date."""
    with app.app_context():
        user = _make_user("checkin@example.com")
        db.session.add(user)
        db.session.flush()

        today = date.today()
        checkin = Checkin(user_id=user.id, checkin_date=today, note="Gut gemacht!")
        db.session.add(checkin)
        db.session.commit()

        result = Checkin.query.filter_by(user_id=user.id, checkin_date=today).first()
        assert result is not None
        assert result.note == "Gut gemacht!"

        yesterday = today - timedelta(days=1)
        assert Checkin.query.filter_by(user_id=user.id, checkin_date=yesterday).first() is None


def test_connection_unique_constraint(app):
    """Inserting a duplicate (user1_id, user2_id) pair raises IntegrityError."""
    with app.app_context():
        u1 = _make_user("dup1@example.com")
        u2 = _make_user("dup2@example.com")
        db.session.add_all([u1, u2])
        db.session.flush()

        db.session.add(Connection(user1_id=u1.id, user2_id=u2.id, status="requested"))
        db.session.commit()

        db.session.add(Connection(user1_id=u1.id, user2_id=u2.id, status="requested"))
        with pytest.raises(IntegrityError):
            db.session.commit()
