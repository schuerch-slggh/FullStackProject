"""Seed the database with 11 dummy profiles.

Run with:  flask --app main seed
All demo accounts share the password:  accountability
"""
import click
import random
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
    dict(
        # streak=0 → keine Check-ins, also auch heute keiner (Test-Ausgangslage).
        user=dict(email="max.muster@example.com", name="Max Muster", age=28, city="Zürich",
                  streak=0,
                  bio="Testnutzer ohne heutigen Check-in. Neu dabei und noch nicht gestartet."),
        photo="https://i.pravatar.cc/300?img=8",
        goals=[
            dict(goal_category="Sport", goal_text="3x pro Woche joggen",
                 frequency="3x pro Woche", preferred_checkin_time="18:00"),
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


_FIRST_NAMES = [
    "Mia", "Noah", "Emma", "Liam", "Sophie", "Elias", "Lea", "Luca", "Laura", "Jan",
    "Nina", "Fabian", "Julia", "Simon", "Anja", "Marco", "Sina", "Reto", "Céline", "Kevin",
    "Chiara", "Dominik", "Aline", "Timo", "Vanessa", "Yannick", "Melanie", "Pascal", "Selina", "Adrian",
    "Michelle", "Raphael", "Jasmin", "Roman", "Carla", "Stefan", "Nadine", "Florian", "Tanja", "Patrick",
    "Larissa", "Dario", "Fiona", "Silvan", "Andrea", "Manuel", "Corinne", "Livio", "Deborah", "Joel",
]

_LAST_NAMES = [
    "Meier", "Müller", "Schmid", "Keller", "Weber", "Huber", "Steiner", "Fischer", "Gerber", "Baumann",
    "Frei", "Brunner", "Moser", "Widmer", "Graf", "Roth", "Zimmermann", "Kunz", "Marti", "Berger",
    "Sutter", "Hofmann", "Schneider", "Wyss", "Lehmann", "Bühler", "Egli", "Meyer", "Stalder", "Blum",
    "Vogel", "Suter", "Furrer", "Ammann", "Kaufmann", "Rey", "Bär", "Peter", "Hess", "Bachmann",
]

_CITIES = [
    "Zürich", "Bern", "Basel", "Genf", "Lausanne", "Luzern", "St. Gallen", "Winterthur",
    "Zug", "Thun", "Chur", "Fribourg", "Aarau", "Solothurn", "Baden", "Uster",
    "Schaffhausen", "Frauenfeld", "Rapperswil", "Wil", "Biel", "Neuenburg", "Sion", "Locarno",
]

_FREQUENCIES = ["täglich", "2x pro Woche", "3x pro Woche", "4x pro Woche", "5x pro Woche"]

_GOAL_TEMPLATES = {
    "Lernen": [
        "Für die Prüfung im Sommer lernen", "Jeden Tag eine Stunde Französisch üben",
        "Online-Kurs in Data Science abschliessen", "Bachelorarbeit fertig schreiben",
        "Englisch auf C1 bringen", "Für die Zwischenprüfung lernen",
    ],
    "Projekt": [
        "Eigene Website launchen", "Nebenbei an einer App bauen", "Portfolio fertigstellen",
        "Business-Plan für Side-Hustle schreiben", "Podcast-Projekt starten",
    ],
    "Sport": [
        "3x pro Woche laufen gehen", "Ins Fitnessstudio gehen", "Für den ersten Halbmarathon trainieren",
        "Wieder regelmässig Yoga machen", "Bouldern 2x pro Woche", "Schwimmtraining aufbauen",
    ],
    "Gewohnheit": [
        "Jeden Abend 20 Minuten lesen", "Früher aufstehen", "Weniger Handyzeit, mehr Fokus",
        "Täglich meditieren", "Feste Schlafenszeit einhalten",
    ],
}

_BIO_TEMPLATES = {
    "Lernen": [
        "Wohne in {city} und will endlich dranbleiben beim Lernen. Suche jemanden, der nachfragt.",
        "Student:in in {city}, brauche einen festen Rhythmus zum Lernen.",
    ],
    "Projekt": [
        "Baue neben dem Studium in {city} an einem eigenen Projekt. Motivation hält besser zu zweit.",
        "Aus {city}. Habe ein Side-Project, das seit Monaten liegen bleibt — jetzt ernsthaft.",
    ],
    "Sport": [
        "Aus {city}, will endlich regelmässig Sport machen. Suche Trainingspartner:in.",
        "Wohne in {city} und brauche jemanden, der mich zum Training mitzieht.",
    ],
    "Gewohnheit": [
        "Aus {city}, will eine neue Gewohnheit durchziehen. Ein Check-in-Partner würde mir enorm helfen.",
        "Lebe in {city} und will alte Muster ändern. Gegenseitige Check-ins helfen mir am meisten.",
    ],
}


def seed_bulk(count: int = 100, rng_seed: int = 42):
    """Insert `count` randomized example users (email user001@example.com ...).

    Idempotent per index: re-running only fills in missing users, matching
    existing profiles are left untouched.
    """
    db.create_all()
    rng = random.Random(rng_seed)
    existing = {u.email for u in User.query.all()}
    created = 0
    for i in range(1, count + 1):
        email = f"user{i:03d}@example.com"
        if email in existing:
            continue
        category = rng.choice(list(_GOAL_TEMPLATES.keys()))
        city = rng.choice(_CITIES)
        user = User(
            email=email,
            name=f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
            age=rng.randint(18, 45),
            city=city,
            bio=rng.choice(_BIO_TEMPLATES[category]).format(city=city),
        )
        user.set_password(DEMO_PASSWORD)
        user.photos.append(Photo(url=f"https://i.pravatar.cc/300?img={rng.randint(1, 70)}", is_primary=True))
        user.goals.append(Goal(
            goal_category=category,
            goal_text=rng.choice(_GOAL_TEMPLATES[category]),
            frequency=rng.choice(_FREQUENCIES),
            preferred_checkin_time=f"{rng.randint(6, 22):02d}:{rng.choice(['00', '15', '30', '45'])}",
        ))
        streak = rng.choice([0, 0, 0, 3, 5, 7, 10, 14, 20])
        for d in range(streak):
            user.checkins.append(Checkin(checkin_date=_date.today() - timedelta(days=d)))
        db.session.add(user)
        created += 1
    db.session.commit()
    return created


def register_cli(app):
    @app.cli.command("seed")
    def seed_command():
        """Insert 11 dummy profiles (skips if the DB already has data)."""
        count = seed_db()
        if count:
            click.echo(f"{count} Profile angelegt. Login z.B.: anna.keller@example.com / {DEMO_PASSWORD}")
        else:
            click.echo("DB enthält bereits Profile - übersprungen.")

    @app.cli.command("seed-bulk")
    @click.option("--count", default=100, help="Anzahl zusätzlicher Beispiel-User")
    def seed_bulk_command(count):
        """Insert additional randomized example users (user001@example.com ...)."""
        created = seed_bulk(count)
        if created:
            click.echo(f"{created} zusätzliche Beispiel-User angelegt (Passwort: {DEMO_PASSWORD}).")
        else:
            click.echo("Alle Beispiel-User existieren bereits - übersprungen.")
