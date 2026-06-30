"""Database entities (ORM models)."""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class User(UserMixin, db.Model):
    """A person and their accountability profile."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    # --- Account / login ---
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # --- Structured profile data ---
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer)
    city = db.Column(db.String(80))
    streak = db.Column(db.Integer, default=0)

    # --- Free text + photo ---
    bio = db.Column(db.Text)
    photo_url = db.Column(db.String(300))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    goals = db.relationship(
        "Goal", back_populates="user",
        order_by="Goal.created_at",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.id} {self.email}>"


class Goal(db.Model):
    """A single commitment belonging to a user."""

    __tablename__ = "goal"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    goal_category = db.Column(db.String(40), nullable=False)
    goal_text = db.Column(db.String(280), nullable=False)
    frequency = db.Column(db.String(40))
    preferred_checkin_time = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<Goal {self.id} user={self.user_id} {self.goal_category}>"
