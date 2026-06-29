"""Seed the database with 10 dummy profiles.

Run with:  flask --app main seed
All demo accounts share the password:  accountability
"""
import click

from . import db
from .models import User

DEMO_PASSWORD = "accountability"

DUMMIES = [
    dict(email="anna.keller@example.com", name="Anna Keller", age=24, city="Zürich",
         goal_category="Lernen", goal_text="Bachelorarbeit fertig schreiben",
         frequency="5x pro Woche", preferred_checkin_time="20:00", streak=12,
         photo_url="https://i.pravatar.cc/300?img=47",
         bio="Wirtschaftsinformatik im letzten Semester. Suche jemanden, der mich beim Schreiben bei der Stange hält."),
    dict(email="luca.bianchi@example.com", name="Luca Bianchi", age=27, city="Winterthur",
         goal_category="Sport", goal_text="3x pro Woche ins Fitnessstudio",
         frequency="3x pro Woche", preferred_checkin_time="07:00", streak=5,
         photo_url="https://i.pravatar.cc/300?img=12",
         bio="Frühaufsteher. Morgensport ist leichter, wenn jemand mitzieht."),
    dict(email="sara.meier@example.com", name="Sara Meier", age=22, city="Zürich",
         goal_category="Gewohnheit", goal_text="Jeden Abend 30 Minuten lesen",
         frequency="täglich", preferred_checkin_time="21:30", streak=31,
         photo_url="https://i.pravatar.cc/300?img=45",
         bio="Will weniger Doomscrolling und mehr Bücher. Aktueller Streak: 31 Tage."),
    dict(email="jonas.weber@example.com", name="Jonas Weber", age=29, city="Basel",
         goal_category="Projekt", goal_text="Eine Web-App nebenbei launchen",
         frequency="4x pro Woche", preferred_checkin_time="19:00", streak=8,
         photo_url="https://i.pravatar.cc/300?img=33",
         bio="Baue abends an einem Side-Project. Brauche jemanden, der nachfragt, ob ich drangeblieben bin."),
    dict(email="mara.fischer@example.com", name="Mara Fischer", age=25, city="Bern",
         goal_category="Sport", goal_text="Halbmarathon im Herbst laufen",
         frequency="4x pro Woche", preferred_checkin_time="18:00", streak=14,
         photo_url="https://i.pravatar.cc/300?img=44",
         bio="Trainiere auf meinen ersten Halbmarathon. Laufpartner:in willkommen."),
    dict(email="david.huber@example.com", name="David Huber", age=31, city="Zürich",
         goal_category="Lernen", goal_text="Spanisch auf B1 bringen",
         frequency="täglich", preferred_checkin_time="08:30", streak=22,
         photo_url="https://i.pravatar.cc/300?img=15",
         bio="20 Minuten Spanisch pro Tag. Suche Lern-Buddy für gegenseitige Check-ins."),
    dict(email="lena.schmid@example.com", name="Lena Schmid", age=23, city="Luzern",
         goal_category="Gewohnheit", goal_text="Früher schlafen, vor 23 Uhr",
         frequency="täglich", preferred_checkin_time="22:30", streak=3,
         photo_url="https://i.pravatar.cc/300?img=49",
         bio="Nachteule, die das ändern will. Abend-Check-in würde mir helfen."),
    dict(email="tom.brunner@example.com", name="Tom Brunner", age=26, city="Winterthur",
         goal_category="Projekt", goal_text="Portfolio-Website fertigstellen",
         frequency="3x pro Woche", preferred_checkin_time="20:30", streak=6,
         photo_url="https://i.pravatar.cc/300?img=51",
         bio="Designer, der seit Monaten an seinem Portfolio rumschiebt. Jetzt ernsthaft."),
    dict(email="nora.graf@example.com", name="Nora Graf", age=28, city="St. Gallen",
         goal_category="Lernen", goal_text="CFA Level 1 vorbereiten",
         frequency="5x pro Woche", preferred_checkin_time="06:30", streak=18,
         photo_url="https://i.pravatar.cc/300?img=20",
         bio="Lerne vor der Arbeit. Suche jemanden mit ähnlichem Pensum und Disziplin."),
    dict(email="finn.koch@example.com", name="Finn Koch", age=21, city="Zürich",
         goal_category="Sport", goal_text="Bouldern 2x pro Woche",
         frequency="2x pro Woche", preferred_checkin_time="17:30", streak=9,
         photo_url="https://i.pravatar.cc/300?img=53",
         bio="Anfänger an der Boulderwand. Motivation hält besser zu zweit."),
]


def seed_db():
    db.create_all()
    if User.query.first():
        return 0
    for data in DUMMIES:
        user = User(**data)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
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
