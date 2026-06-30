"""Seed the database with 10 dummy profiles.

Run with:  flask --app main seed
All demo accounts share the password:  accountability
"""
import click
from datetime import timedelta, date as _date, datetime

from . import db
from .models import User, Goal, Photo, Connection, Message, Checkin, Rating

DEMO_PASSWORD = "accountability"

DUMMIES = [
    dict(
        user=dict(email="anna.keller@example.com", name="Anna Keller", age=24, city="Zürich",
                  streak=12,
                  bio="Wirtschaftsinformatik im letzten Semester. Suche jemanden, der mich beim Schreiben bei der Stange hält."),
        photo="https://i.pravatar.cc/300?img=47",
        goals=[
            dict(goal_category="Lernen", goal_text="Bachelorarbeit fertig schreiben",
                 frequency="5x pro Woche", preferred_checkin_time="20:00"),
        ],
    ),
    dict(
        user=dict(email="luca.bianchi@example.com", name="Luca Bianchi", age=27, city="Winterthur",
                  streak=5,
                  bio="Frühaufsteher. Morgensport ist leichter, wenn jemand mitzieht."),
        photo="https://i.pravatar.cc/300?img=12",
        goals=[
            dict(goal_category="Sport", goal_text="3x pro Woche ins Fitnessstudio",
                 frequency="3x pro Woche", preferred_checkin_time="07:00"),
        ],
    ),
    dict(
        user=dict(email="sara.meier@example.com", name="Sara Meier", age=22, city="Zürich",
                  streak=31,
                  bio="Will weniger Doomscrolling und mehr Bücher. Aktueller Streak: 31 Tage."),
        photo="https://i.pravatar.cc/300?img=45",
        goals=[
            dict(goal_category="Gewohnheit", goal_text="Jeden Abend 30 Minuten lesen",
                 frequency="täglich", preferred_checkin_time="21:30"),
        ],
    ),
    dict(
        user=dict(email="jonas.weber@example.com", name="Jonas Weber", age=29, city="Basel",
                  streak=8,
                  bio="Baue abends an einem Side-Project. Brauche jemanden, der nachfragt, ob ich drangeblieben bin."),
        photo="https://i.pravatar.cc/300?img=33",
        goals=[
            dict(goal_category="Projekt", goal_text="Eine Web-App nebenbei launchen",
                 frequency="4x pro Woche", preferred_checkin_time="19:00"),
            dict(goal_category="Lernen", goal_text="TypeScript lernen",
                 frequency="3x pro Woche", preferred_checkin_time="21:00"),
        ],
    ),
    dict(
        user=dict(email="mara.fischer@example.com", name="Mara Fischer", age=25, city="Bern",
                  streak=14,
                  bio="Trainiere auf meinen ersten Halbmarathon. Laufpartner:in willkommen."),
        photo="https://i.pravatar.cc/300?img=44",
        goals=[
            dict(goal_category="Sport", goal_text="Halbmarathon im Herbst laufen",
                 frequency="4x pro Woche", preferred_checkin_time="18:00"),
        ],
    ),
    dict(
        user=dict(email="david.huber@example.com", name="David Huber", age=31, city="Zürich",
                  streak=22,
                  bio="20 Minuten Spanisch pro Tag. Suche Lern-Buddy für gegenseitige Check-ins."),
        photo="https://i.pravatar.cc/300?img=15",
        goals=[
            dict(goal_category="Lernen", goal_text="Spanisch auf B1 bringen",
                 frequency="täglich", preferred_checkin_time="08:30"),
            dict(goal_category="Gewohnheit", goal_text="Täglich meditieren",
                 frequency="täglich", preferred_checkin_time="07:30"),
        ],
    ),
    dict(
        user=dict(email="lena.schmid@example.com", name="Lena Schmid", age=23, city="Luzern",
                  streak=3,
                  bio="Nachteule, die das ändern will. Abend-Check-in würde mir helfen."),
        photo="https://i.pravatar.cc/300?img=49",
        goals=[
            dict(goal_category="Gewohnheit", goal_text="Früher schlafen, vor 23 Uhr",
                 frequency="täglich", preferred_checkin_time="22:30"),
        ],
    ),
    dict(
        user=dict(email="tom.brunner@example.com", name="Tom Brunner", age=26, city="Winterthur",
                  streak=6,
                  bio="Designer, der seit Monaten an seinem Portfolio rumschiebt. Jetzt ernsthaft."),
        photo="https://i.pravatar.cc/300?img=51",
        goals=[
            dict(goal_category="Projekt", goal_text="Portfolio-Website fertigstellen",
                 frequency="3x pro Woche", preferred_checkin_time="20:30"),
        ],
    ),
    dict(
        user=dict(email="nora.graf@example.com", name="Nora Graf", age=28, city="St. Gallen",
                  streak=18,
                  bio="Lerne vor der Arbeit. Suche jemanden mit ähnlichem Pensum und Disziplin."),
        photo="https://i.pravatar.cc/300?img=20",
        goals=[
            dict(goal_category="Lernen", goal_text="CFA Level 1 vorbereiten",
                 frequency="5x pro Woche", preferred_checkin_time="06:30"),
        ],
    ),
    dict(
        user=dict(email="finn.koch@example.com", name="Finn Koch", age=21, city="Zürich",
                  streak=9,
                  bio="Anfänger an der Boulderwand. Motivation hält besser zu zweit."),
        photo="https://i.pravatar.cc/300?img=53",
        goals=[
            dict(goal_category="Sport", goal_text="Bouldern 2x pro Woche",
                 frequency="2x pro Woche", preferred_checkin_time="17:30"),
        ],
    ),
]

# (email_user1, email_user2, status)
_CONNECTIONS = [
    ("anna.keller@example.com", "luca.bianchi@example.com", "active"),
    ("sara.meier@example.com", "mara.fischer@example.com", "active"),
    ("jonas.weber@example.com", "david.huber@example.com", "active"),
    ("finn.koch@example.com", "nora.graf@example.com", "requested"),
]

# (rater_email, ratee_email, stars) — gegenseitige Bewertungen aktiver Partner (FA-13)
_RATINGS = [
    ("anna.keller@example.com", "luca.bianchi@example.com", 5),
    ("luca.bianchi@example.com", "anna.keller@example.com", 4),
    ("sara.meier@example.com", "mara.fischer@example.com", 5),
    ("mara.fischer@example.com", "sara.meier@example.com", 5),
    ("jonas.weber@example.com", "david.huber@example.com", 4),
    ("david.huber@example.com", "jonas.weber@example.com", 5),
]

# (connection_index into active connections, sender_email, text, days_ago)
_MESSAGES = [
    (0, "anna.keller@example.com", "Hey, check-in für heute Abend?", 5),
    (0, "luca.bianchi@example.com", "Ja! Ich war heute früh laufen.", 5),
    (0, "anna.keller@example.com", "Super, ich hab 2 Stunden geschrieben 💪", 4),
    (1, "sara.meier@example.com", "Wie läuft dein Training?", 3),
    (1, "mara.fischer@example.com", "Heute 10 km — neuer Rekord!", 3),
    (1, "sara.meier@example.com", "Respekt! Ich hab heute 40 Seiten gelesen.", 2),
    (2, "jonas.weber@example.com", "Hast du heute Spanisch gemacht?", 2),
    (2, "david.huber@example.com", "Klar, Lektion 7 erledigt!", 2),
    (2, "jonas.weber@example.com", "Nice. Ich hab 3 Stunden am Projekt gebaut.", 1),
]

def seed_db():
    db.create_all()
    if User.query.first():
        return 0

    # --- Users, Goals, Photos ---
    # The `streak` value in each dummy drives a run of consecutive daily
    # check-ins below; the streak itself is computed from those (no column).
    streaks = {}
    for entry in DUMMIES:
        udata = dict(entry["user"])
        streaks[udata["email"]] = udata.pop("streak", 0)
        user = User(**udata)
        user.set_password(DEMO_PASSWORD)
        user.photos.append(Photo(url=entry["photo"], is_primary=True))
        for g in entry["goals"]:
            user.goals.append(Goal(**g))
        db.session.add(user)
    db.session.commit()

    # --- Connections ---
    users = {u.email: u for u in User.query.all()}
    conn_objects = []
    for email1, email2, status in _CONNECTIONS:
        conn = Connection(
            user1_id=users[email1].id,
            user2_id=users[email2].id,
            status=status,
        )
        db.session.add(conn)
        conn_objects.append((conn, email1, email2))
    db.session.commit()

    # Re-fetch to get IDs; only index the active ones for messages
    active_conns = [c for c in Connection.query.all() if c.status == "active"]

    # --- Messages ---
    today = datetime.utcnow()
    for conn_idx, sender_email, text, days_ago in _MESSAGES:
        if conn_idx >= len(active_conns):
            continue
        conn = active_conns[conn_idx]
        sent_at = today - timedelta(days=days_ago)
        msg = Message(
            connection_id=conn.id,
            sender_id=users[sender_email].id,
            text=text,
            sent_at=sent_at,
            # Seed-Nachrichten sind älter und gelten als gelesen (FA-16 AK1).
            read_at=sent_at,
        )
        db.session.add(msg)

    # --- Checkins: a run of consecutive days (today backwards) per user,
    # so the computed streak matches the intended demo value. ---
    today_date = _date.today()
    for email, streak in streaks.items():
        u = users[email]
        for d in range(streak):
            db.session.add(Checkin(
                user_id=u.id,
                checkin_date=today_date - timedelta(days=d),
            ))

    # --- Ratings: gegenseitige Partner-Bewertungen (FA-13) ---
    for rater_email, ratee_email, stars in _RATINGS:
        db.session.add(Rating(
            rater_id=users[rater_email].id,
            ratee_id=users[ratee_email].id,
            stars=stars,
        ))

    db.session.commit()
    return len(DUMMIES)


def register_cli(app):
    @app.cli.command("seed")
    def seed_command():
        """Insert 10 dummy profiles (skips if the DB already has data)."""
        count = seed_db()
        if count:
            click.echo(f"{count} Profile angelegt. Login z.B.: anna.keller@example.com / {DEMO_PASSWORD}")
        else:
            click.echo("DB enthält bereits Profile - übersprungen.")
