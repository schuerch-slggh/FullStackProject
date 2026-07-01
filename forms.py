from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, SubmitField,
    SelectField, IntegerField, TextAreaField, BooleanField,
)
from wtforms.fields import TimeField
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError,
)

from .models import User

GOAL_CATEGORIES = [
    ("Lernen", "Lernen"),
    ("Projekt", "Projekt"),
    ("Sport", "Sport"),
    ("Gewohnheit", "Gewohnheit"),
    ("Kreativität", "Kreativität"),
    ("Finanzen", "Finanzen"),
    ("Karriere", "Karriere"),
    ("Achtsamkeit", "Achtsamkeit"),
]

FREQUENCY_CHOICES = [
    ("", "Alle"),
    ("täglich", "täglich"),
    ("2x pro Woche", "2x pro Woche"),
    ("3x pro Woche", "3x pro Woche"),
    ("4x pro Woche", "4x pro Woche"),
    ("5x pro Woche", "5x pro Woche"),
]

# Für die zwei Dropdowns beim Anlegen eines Commitments (statt Freitext).
FREQUENCY_COUNT_CHOICES = [(str(i), str(i)) for i in range(1, 11)]
FREQUENCY_UNIT_CHOICES = [
    ("täglich", "täglich"),
    ("wöchentlich", "wöchentlich"),
    ("monatlich", "monatlich"),
]


def compose_frequency(count: str, unit: str) -> str:
    """Turn the two frequency dropdowns into the stored string.

    Kept compatible with the existing "täglich" / "Nx pro Woche" convention
    (used by seed data and the search filter) so matching keeps working;
    "monatlich" extends it with "Nx pro Monat".
    """
    if unit == "täglich":
        return "täglich"
    period = "Woche" if unit == "wöchentlich" else "Monat"
    return f"{count}x pro {period}"


class LoginForm(FlaskForm):
    email = StringField("E-Mail", validators=[DataRequired(), Email()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Anmelden")


class RegistrationForm(FlaskForm):
    # --- Konto ---
    email = StringField("E-Mail", validators=[DataRequired(), Email()])
    password = PasswordField("Passwort", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField(
        "Passwort bestätigen",
        validators=[DataRequired(), EqualTo("password", message="Passwörter stimmen nicht überein.")],
    )

    # --- Identität ---
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    age = IntegerField("Alter", validators=[Optional(), NumberRange(min=14, max=120)])
    city = StringField("Ort", validators=[Optional(), Length(max=80)])

    # --- Erstes Commitment ---
    goal_category = SelectField("Zielkategorie", choices=GOAL_CATEGORIES, validators=[DataRequired()])
    goal_text = StringField("Dein konkretes Ziel", validators=[DataRequired(), Length(max=280)])
    frequency_count = SelectField("Anzahl", choices=FREQUENCY_COUNT_CHOICES, default="3")
    frequency_unit = SelectField("Rhythmus", choices=FREQUENCY_UNIT_CHOICES, default="wöchentlich")
    preferred_checkin_time = TimeField(
        "Bevorzugte Check-in-Zeit", validators=[Optional()], format="%H:%M",
    )

    bio = TextAreaField("Über mich", validators=[Optional(), Length(max=500)])

    submit = SubmitField("Konto erstellen")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("Diese E-Mail ist bereits registriert.")


class EditProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    age = IntegerField("Alter", validators=[Optional(), NumberRange(min=14, max=120)])
    city = StringField("Ort", validators=[Optional(), Length(max=80)])
    bio = TextAreaField("Über mich", validators=[Optional(), Length(max=500)])
    photo = FileField("Profilfoto", validators=[
        Optional(),
        FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Nur Bilddateien erlaubt."),
    ])
    submit = SubmitField("Speichern")


class GoalForm(FlaskForm):
    goal_category = SelectField("Zielkategorie", choices=GOAL_CATEGORIES, validators=[DataRequired()])
    goal_text = StringField("Dein Ziel", validators=[DataRequired(), Length(max=280)])
    frequency_count = SelectField("Anzahl", choices=FREQUENCY_COUNT_CHOICES, default="3")
    frequency_unit = SelectField("Rhythmus", choices=FREQUENCY_UNIT_CHOICES, default="wöchentlich")
    preferred_checkin_time = TimeField(
        "Bevorzugte Check-in-Zeit", validators=[Optional()], format="%H:%M",
    )
    submit = SubmitField("Commitment speichern")


class SearchForm(FlaskForm):
    """Partner search form — submitted via GET, so CSRF is disabled."""

    class Meta:
        csrf = False

    category = SelectField(
        "Kategorie",
        choices=[("", "Alle")] + GOAL_CATEGORIES,
    )
    frequency = SelectField("Frequenz", choices=FREQUENCY_CHOICES)
    city = StringField("Stadt / Ort", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Suchen")


class MessageForm(FlaskForm):
    text = TextAreaField("Nachricht", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Senden")


class CheckinForm(FlaskForm):
    """Mark a check-in for today. `goal.choices` is set per request in the view."""

    goal = SelectField("Ziel", validators=[Optional()])
    note = StringField("Notiz (optional)", validators=[Optional(), Length(max=280)])
    submit = SubmitField("Heute einchecken")


class SettingsForm(FlaskForm):
    """Nutzereinstellungen — E-Mail-Notification an/aus (FA-10 AK2)."""

    notify_email = BooleanField("E-Mail-Benachrichtigungen aktivieren")
    submit = SubmitField("Speichern")


class CoachGoalForm(FlaskForm):
    """Vages Ziel, das der KI-Coach konkreter formuliert (FA-11 AK2)."""

    goal_text = TextAreaField("Dein Ziel", validators=[DataRequired(), Length(max=280)])
    submit = SubmitField("Konkreter machen")


class RatingForm(FlaskForm):
    """Bewertung eines Partners als Accountability-Buddy (FA-13 AK2)."""

    stars = SelectField(
        "Bewertung",
        choices=[("5", "★★★★★"), ("4", "★★★★"), ("3", "★★★"), ("2", "★★"), ("1", "★")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Bewertung speichern")
