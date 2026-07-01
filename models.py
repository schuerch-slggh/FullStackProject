"""Database entities (ORM models) and domain helpers."""
from datetime import datetime, date, time, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

# Sliding window for the activity component of the reputation score (FA-13).
REPUTATION_WINDOW_DAYS = 14
# How long after the last request a user still counts as "online" (FA-16 AK2).
ONLINE_WINDOW_SECONDS = 300


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

    # Zuletzt aktiv — Basis für den Online-Status im Chat (FA-16 AK2).
    last_seen = db.Column(db.DateTime)

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
    ratings_received = db.relationship(
        "Rating",
        foreign_keys="Rating.ratee_id",
        back_populates="ratee",
        cascade="all, delete-orphan",
    )
    ratings_given = db.relationship(
        "Rating",
        foreign_keys="Rating.rater_id",
        back_populates="rater",
        cascade="all, delete-orphan",
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

    @property
    def activity_level(self):
        """Share of the last 14 days with at least one check-in (0.0–1.0).

        The measurable activity component of the reputation score (FA-13 AK1):
        how reliably the user actually checks in.
        """
        window = {date.today() - timedelta(days=d) for d in range(REPUTATION_WINDOW_DAYS)}
        done = {c.checkin_date for c in self.checkins if c.checkin_date in window}
        return len(done) / REPUTATION_WINDOW_DAYS

    @property
    def avg_rating(self):
        """Average star rating from partners, or None if not yet rated (FA-13 AK2)."""
        ratings = self.ratings_received
        return sum(r.stars for r in ratings) / len(ratings) if ratings else None

    @property
    def reputation(self):
        """Reliability score 0.0–5.0 (FA-13): blends activity and partner ratings.

        Without any ratings the score is the activity level scaled to five
        stars; once partners have rated the user, activity and the average
        rating are weighted equally. Visible on the profile and used as the
        tie-breaker in the match ordering (FA-13 AK3).
        """
        activity_stars = self.activity_level * 5
        if self.avg_rating is None:
            return round(activity_stars, 1)
        return round((activity_stars + self.avg_rating) / 2, 1)

    @property
    def is_online(self):
        """True if the user was active within the last few minutes (FA-16 AK2)."""
        if self.last_seen is None:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() < ONLINE_WINDOW_SECONDS

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
    # Gesetzt, sobald der Empfänger den Chat öffnet (FA-16 AK1). NULL = ungelesen.
    read_at = db.Column(db.DateTime)

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


class Rating(db.Model):
    """A reliability rating one partner gives another (FA-13 AK2).

    A user can hold at most one rating per partner; re-rating updates it.
    """

    __tablename__ = "rating"
    __table_args__ = (
        db.UniqueConstraint("rater_id", "ratee_id", name="uq_rating_pair"),
    )

    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    ratee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    stars = db.Column(db.Integer, nullable=False)  # 1–5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rater = db.relationship("User", foreign_keys=[rater_id], back_populates="ratings_given")
    ratee = db.relationship("User", foreign_keys=[ratee_id], back_populates="ratings_received")

    def __repr__(self):
        return f"<Rating {self.id} {self.rater_id}→{self.ratee_id} {self.stars}★>"


# Named so the UI can show *why* two users matched, not just the percentage.
MATCH_CRITERIA = (
    ("category", "gleiche Zielkategorie", 2),
    ("frequency", "passende Frequenz", 1),
    ("checkin_time", "passende Check-in-Zeit", 1),
)
MATCH_MAX_SCORE = sum(points for _, _, points in MATCH_CRITERIA)


def _shared_criteria(user_a: User, user_b: User) -> "dict[str, bool]":
    """Which of the three match criteria user_a and user_b share, across all goals."""
    cats_a = {g.goal_category for g in user_a.goals}
    cats_b = {g.goal_category for g in user_b.goals}
    freqs_a = {g.frequency for g in user_a.goals if g.frequency}
    freqs_b = {g.frequency for g in user_b.goals if g.frequency}
    times_a = {g.preferred_checkin_time for g in user_a.goals if g.preferred_checkin_time}
    times_b = {g.preferred_checkin_time for g in user_b.goals if g.preferred_checkin_time}
    return {
        "category": bool(cats_a & cats_b),
        "frequency": bool(freqs_a & freqs_b),
        "checkin_time": bool(times_a & times_b),
    }


def _breakdown_from_shared(shared: "dict[str, bool]") -> "list[dict]":
    return [
        {"label": label, "matched": shared[key], "points": points}
        for key, label, points in MATCH_CRITERIA
    ]


def match_score(user_a: User, user_b: User) -> int:
    """Match score between two users based on goal overlap (0–4).

    +2  at least one shared goal category
    +1  at least one shared frequency
    +1  at least one shared preferred check-in time
    """
    shared = _shared_criteria(user_a, user_b)
    return sum(points for key, _, points in MATCH_CRITERIA if shared[key])


def match_breakdown(user_a: User, user_b: User) -> "list[dict]":
    """Per-criterion detail behind `match_score`, for UI transparency.

    Returns one dict per criterion with `label`, `matched` and `points`, so
    the search/matches views can show *why* a percentage came out as it did.
    """
    return _breakdown_from_shared(_shared_criteria(user_a, user_b))


def _goal_shared_criteria(goal: "Goal", user: User) -> "dict[str, bool]":
    """Which criteria `user` shares with one specific goal (Matches tab, FA-05)."""
    same_category = [g for g in user.goals if g.goal_category == goal.goal_category]
    return {
        "category": bool(same_category),
        "frequency": bool(
            goal.frequency and any(g.frequency == goal.frequency for g in same_category)
        ),
        "checkin_time": bool(
            goal.preferred_checkin_time
            and any(g.preferred_checkin_time == goal.preferred_checkin_time for g in same_category)
        ),
    }


def match_breakdown_for_goal(goal: "Goal", user: User) -> "list[dict]":
    """Per-criterion detail behind one goal's match score (Matches tab)."""
    return _breakdown_from_shared(_goal_shared_criteria(goal, user))


def top_matches_for_goal(goal: "Goal", limit: int = 3) -> "list[tuple[User, int]]":
    """Best `limit` other users for one specific goal (FA-05, scoped per goal).

    Unlike `match_score` (which compares a user's whole goal set), this looks
    only at the given goal so the "Matches" tab can show relevant partners per
    commitment. Candidates need at least one goal in the same category (+2);
    a shared frequency or check-in time on that goal add +1 each (0–4, same
    scale as `match_score`). Ties break by reputation (FA-13 AK3).
    """
    candidates = (
        User.query.join(Goal)
        .filter(Goal.goal_category == goal.goal_category, User.id != goal.user_id)
        .distinct()
        .all()
    )
    scored = [
        (user, sum(points for key, _, points in MATCH_CRITERIA if _goal_shared_criteria(goal, user)[key]))
        for user in candidates
    ]
    scored.sort(key=lambda pair: (pair[1], pair[0].reputation), reverse=True)
    return scored[:limit]


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


def checkin_history(user: User, *, days: int = 14, today: date = None) -> "list[dict]":
    """Per-day check-in counts over the last `days` days (FA-12 AK2).

    Returns a chronological list (oldest first) of `{"date", "count"}`, ready to
    render as a simple progress chart. `today` is injectable for deterministic
    tests.
    """
    today = today or date.today()
    counts = {}
    for c in user.checkins:
        counts[c.checkin_date] = counts.get(c.checkin_date, 0) + 1
    return [
        {"date": today - timedelta(days=d), "count": counts.get(today - timedelta(days=d), 0)}
        for d in reversed(range(days))
    ]
