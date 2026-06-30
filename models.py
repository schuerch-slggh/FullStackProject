"""Database entities (ORM models) and domain helpers."""
from datetime import datetime, date, time

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

    # --- Free text ---
    bio = db.Column(db.Text)

    # --- Settings ---
    # E-Mail-Notification an/aus (FA-10 AK2); default an.
    notify_email = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    goals = db.relationship(
        "Goal", back_populates="user",
        order_by="Goal.created_at",
        cascade="all, delete-orphan",
    )
    photos = db.relationship(
        "Photo", back_populates="user",
        order_by="Photo.uploaded_at",
        cascade="all, delete-orphan",
    )
    checkins = db.relationship(
        "Checkin", back_populates="user",
        order_by="Checkin.checkin_date",
        cascade="all, delete-orphan",
    )
    connections_sent = db.relationship(
        "Connection",
        foreign_keys="Connection.user1_id",
        back_populates="user1",
    )
    connections_received = db.relationship(
        "Connection",
        foreign_keys="Connection.user2_id",
        back_populates="user2",
    )
    messages_sent = db.relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
    )

    @property
    def photo_url(self):
        primary = next((p for p in self.photos if p.is_primary), None)
        return primary.url if primary else (self.photos[-1].url if self.photos else None)

    @property
    def streak(self):
        """Consecutive-day check-in streak (FA-08).

        Counts back from the most recent check-in. A check-in today or
        yesterday keeps the chain alive (so the streak does not drop to 0 just
        because today's check-in is still pending); any larger gap breaks it
        and the streak resets (FA-08 AK2). Each new daily check-in extends the
        chain by one (FA-08 AK1).
        """
        days = sorted({c.checkin_date for c in self.checkins}, reverse=True)
        if not days or (date.today() - days[0]).days > 1:
            return 0
        streak = 1
        for newer, older in zip(days, days[1:]):
            if (newer - older).days == 1:
                streak += 1
            else:
                break
        return streak

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
    checkins = db.relationship("Checkin", back_populates="goal")

    def __repr__(self):
        return f"<Goal {self.id} user={self.user_id} {self.goal_category}>"


class Photo(db.Model):
    """A profile photo belonging to a user."""

    __tablename__ = "photo"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    url = db.Column(db.String(300), nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="photos")

    def __repr__(self):
        return f"<Photo {self.id} user={self.user_id} primary={self.is_primary}>"


class Connection(db.Model):
    """An accountability partnership between two users."""

    __tablename__ = "connection"
    __table_args__ = (
        db.UniqueConstraint("user1_id", "user2_id", name="uq_connection_pair"),
        db.Index("ix_connection_user1_status", "user1_id", "status"),
        db.Index("ix_connection_user2_status", "user2_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # user1 is the initiator, user2 is the receiver
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="requested")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user1 = db.relationship("User", foreign_keys=[user1_id], back_populates="connections_sent")
    user2 = db.relationship("User", foreign_keys=[user2_id], back_populates="connections_received")
    messages = db.relationship(
        "Message", back_populates="connection",
        order_by="Message.sent_at",
        cascade="all, delete-orphan",
    )

    @classmethod
    def between(cls, user_a_id: int, user_b_id: int) -> "Connection | None":
        """Return the connection between two users regardless of direction."""
        return cls.query.filter(
            db.or_(
                db.and_(cls.user1_id == user_a_id, cls.user2_id == user_b_id),
                db.and_(cls.user1_id == user_b_id, cls.user2_id == user_a_id),
            )
        ).first()

    @classmethod
    def active_for(cls, user_id: int) -> "list[Connection]":
        """All active partnerships a user is part of, newest activity first."""
        return cls.query.filter(
            cls.status == "active",
            db.or_(cls.user1_id == user_id, cls.user2_id == user_id),
        ).order_by(cls.updated_at.desc()).all()

    def involves(self, user_id: int) -> bool:
        """True if the user is one of the two partners (access gate)."""
        return user_id in (self.user1_id, self.user2_id)

    def partner_of(self, user: "User") -> "User":
        """The other partner relative to the given user."""
        return self.user2 if self.user1_id == user.id else self.user1

    def __repr__(self):
        return f"<Connection {self.id} {self.user1_id}↔{self.user2_id} {self.status}>"


class Message(db.Model):
    """A single chat message within a connection."""

    __tablename__ = "message"
    __table_args__ = (
        db.Index("ix_message_conn_time", "connection_id", "sent_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey("connection.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    connection = db.relationship("Connection", back_populates="messages")
    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")

    def __repr__(self):
        return f"<Message {self.id} conn={self.connection_id} from={self.sender_id}>"


class Checkin(db.Model):
    """A daily accountability check-in by a user."""

    __tablename__ = "checkin"
    __table_args__ = (
        db.Index("ix_checkin_user_date", "user_id", "checkin_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goal.id"), nullable=True, index=True)
    checkin_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="checkins")
    goal = db.relationship("Goal", back_populates="checkins")

    def __repr__(self):
        return f"<Checkin {self.id} user={self.user_id} date={self.checkin_date}>"


def match_score(user_a: User, user_b: User) -> int:
    """Match score between two users based on goal overlap (0–4).

    +2  at least one shared goal category
    +1  at least one shared frequency
    +1  at least one shared preferred check-in time
    """
    cats_a = {g.goal_category for g in user_a.goals}
    cats_b = {g.goal_category for g in user_b.goals}
    freqs_a = {g.frequency for g in user_a.goals if g.frequency}
    freqs_b = {g.frequency for g in user_b.goals if g.frequency}
    times_a = {g.preferred_checkin_time for g in user_a.goals if g.preferred_checkin_time}
    times_b = {g.preferred_checkin_time for g in user_b.goals if g.preferred_checkin_time}

    score = 0
    if cats_a & cats_b:
        score += 2
    if freqs_a & freqs_b:
        score += 1
    if times_a & times_b:
        score += 1
    return score


def _parse_time(value: str) -> "time | None":
    """Parse a preferred check-in time like '08:00' into a time, else None."""
    try:
        hh, mm = value.strip().split(":")
        return time(int(hh), int(mm))
    except (ValueError, AttributeError):
        return None


def due_reminders(user: User, *, now: datetime = None) -> "list[Goal]":
    """Goals whose check-in is due now and not yet done today (FA-09).

    The schedule is the goal's frequency + preferred check-in time (FA-09 AK1).
    A goal counts as due (FA-09 AK2) when it has a preferred check-in time, that
    time has passed for today, and no check-in exists for that goal today.
    `now` is injectable so the trigger is deterministic and testable.
    """
    now = now or datetime.now()
    today = now.date()
    done_goal_ids = {c.goal_id for c in user.checkins if c.checkin_date == today}
    due = []
    for goal in user.goals:
        if goal.id in done_goal_ids:
            continue
        scheduled = _parse_time(goal.preferred_checkin_time) if goal.preferred_checkin_time else None
        if scheduled is not None and now.time() >= scheduled:
            due.append(goal)
    return due
