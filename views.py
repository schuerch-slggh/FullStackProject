"""Main controller: landing page, profile, goal management, search,
connections, chat & check-in."""
import os
from collections import Counter
from datetime import date, datetime, timedelta

from flask import (
    Blueprint, render_template, redirect, url_for, flash, current_app,
    abort, request, jsonify,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import (
    User, Goal, Photo, Connection, Message, Checkin, Rating,
    match_score, top_matches_for_goal, due_reminders, checkin_history,
)
from .forms import (
    EditProfileForm, GoalForm, SearchForm, MessageForm, CheckinForm,
    SettingsForm, RatingForm,
)
from .mailer import notify
from .coach import chat_reply, coach_headline

main_bp = Blueprint("main", __name__)


def _goal_choices(user):
    """Check-in goal options: a general entry plus the user's own goals."""
    return [("", "Allgemein")] + [(str(g.id), g.goal_text) for g in user.goals]


def _checked_in_today(user):
    return Checkin.query.filter_by(
        user_id=user.id, checkin_date=date.today()
    ).first() is not None


@main_bp.before_app_request
def _touch_last_seen():
    """Track activity for the online status (FA-16 AK2), throttled to one write
    per minute so it doesn't add a commit to every request."""
    if not current_user.is_authenticated:
        return
    now = datetime.utcnow()
    last = current_user.last_seen
    if last is None or (now - last).total_seconds() > 60:
        current_user.last_seen = now
        db.session.commit()


# Streak-Schwellen, die im Aktivitäts-Feed als Meilenstein hervorgehoben werden.
_STREAK_MILESTONES = {3, 7, 14, 21, 30, 50, 75, 100, 150, 200, 365}


def _relative_when(when: datetime, today: date) -> str:
    """Kurzes Mono-taugliches Zeitlabel für den Feed (heute/gestern/Datum)."""
    delta = (today - when.date()).days
    if delta <= 0:
        return f"heute {when.strftime('%H:%M')}"
    if delta == 1:
        return "gestern"
    if delta < 7:
        return f"vor {delta} Tagen"
    return when.strftime("%d.%m.")


def _partner_activity(partner_conns, *, days: int = 7, limit: int = 20):
    """Chronologische Ereignisse der eigenen Partner (FA-12/FA-08, read-only).

    Baut den Aktivitäts-Feed rein aus vorhandenen Daten: Check-ins der letzten
    `days` Tage und aktuelle Streak-Meilensteine. Zugriffsschutz ist inhärent —
    es werden nur die übergebenen (eigenen) Partnerschaften ausgewertet.
    """
    today = date.today()
    cutoff = today - timedelta(days=days)
    events = []
    for conn in partner_conns:
        partner = conn.partner_of(current_user)

        for c in partner.checkins:
            if c.checkin_date < cutoff:
                continue
            when = c.created_at or datetime.combine(c.checkin_date, datetime.min.time())
            heute = c.checkin_date == today
            events.append({
                "icon": "✓",
                "text": f"{partner.name} hat {'heute ' if heute else ''}eingecheckt"
                        + ("" if heute else f" ({c.checkin_date.strftime('%d.%m.')})"),
                "when": _relative_when(when, today),
                "sort": when,
                "milestone": False,
            })

        # Streak-Meilenstein: nur wenn die aktuelle Streak eine Schwelle trifft
        # und der Lauf noch aktiv ist (letzter Check-in im Fenster).
        streak = partner.streak
        if streak in _STREAK_MILESTONES and partner.checkins:
            last = max(c.checkin_date for c in partner.checkins)
            if last >= cutoff:
                when = datetime.combine(last, datetime.max.time())
                events.append({
                    "icon": "★",
                    "text": f"{partner.name} hat eine Streak von {streak} Tagen erreicht",
                    "when": _relative_when(when, today),
                    "sort": when,
                    "milestone": True,
                })

    events.sort(key=lambda e: e["sort"], reverse=True)
    return events[:limit]


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.grindprogress"))
    return render_template("landing.html")


@main_bp.route("/grindprogress")
@login_required
def grindprogress():
    """Startseite: eigenes Check-in/Fortschritts-Dashboard + Partner & Feed."""
    partners = Connection.active_for(current_user.id)
    checkin_form = CheckinForm()
    checkin_form.goal.choices = _goal_choices(current_user)
    # Kompakte Partner-Fortschritte (7-Tage-Mini-Gitter) für die Übersicht.
    partner_progress = [
        {
            "conn": conn,
            "partner": conn.partner_of(current_user),
            "history": checkin_history(conn.partner_of(current_user), days=7),
        }
        for conn in partners
    ]
    return render_template(
        "grindprogress.html",
        user=current_user,
        checkin_form=checkin_form,
        checked_in_today=_checked_in_today(current_user),
        reminders=due_reminders(current_user),
        history=checkin_history(current_user),
        partner_progress=partner_progress,
        feed=_partner_activity(partners),
    )


@main_bp.route("/profile")
@login_required
def profile():
    pending_requests = Connection.query.filter_by(
        user2_id=current_user.id, status="requested"
    ).all()
    partners = Connection.active_for(current_user.id)
    return render_template(
        "profile.html",
        user=current_user,
        pending_requests=pending_requests,
        partners=partners,
    )


@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.age = form.age.data
        current_user.city = form.city.data
        current_user.bio = form.bio.data

        photo_file = form.photo.data
        if photo_file and photo_file.filename:
            filename = secure_filename(f"{current_user.id}_{photo_file.filename}")
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            photo_file.save(upload_path)
            for p in current_user.photos:
                p.is_primary = False
            db.session.add(Photo(
                user_id=current_user.id,
                url=url_for("static", filename=f"uploads/{filename}"),
                is_primary=True,
            ))

        db.session.commit()
        flash("Profil gespeichert.", "success")
        return redirect(url_for("main.profile"))

    return render_template("edit_profile.html", form=form)


@main_bp.route("/goals/new", methods=["GET", "POST"])
@login_required
def add_goal():
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user.id,
            goal_category=form.goal_category.data,
            goal_text=form.goal_text.data,
            frequency=form.frequency.data,
            preferred_checkin_time=form.preferred_checkin_time.data,
        )
        db.session.add(goal)
        db.session.commit()
        flash("Commitment hinzugefügt.", "success")
        return redirect(url_for("main.profile"))
    return render_template("goal_form.html", form=form)


@main_bp.route("/goals/<int:goal_id>/delete", methods=["POST"])
@login_required
def delete_goal(goal_id):
    goal = db.get_or_404(Goal, goal_id)
    if goal.user_id != current_user.id:
        abort(403)
    db.session.delete(goal)
    db.session.commit()
    flash("Commitment entfernt.", "info")
    return redirect(url_for("main.profile"))


@main_bp.route("/u/<int:user_id>")
@login_required
def user_profile(user_id):
    user = db.get_or_404(User, user_id)
    connection = Connection.between(current_user.id, user_id)
    my_rating = Rating.query.filter_by(
        rater_id=current_user.id, ratee_id=user_id
    ).first()
    rating_form = RatingForm()
    if my_rating:
        rating_form.stars.data = str(my_rating.stars)
    return render_template(
        "user_profile.html", user=user, connection=connection,
        rating_form=rating_form, my_rating=my_rating,
    )


@main_bp.route("/search")
@login_required
def search():
    form = SearchForm(request.args)
    results = []
    searched = "submit" in request.args

    if searched and form.validate():
        query = User.query.filter(User.id != current_user.id)

        if form.category.data or form.frequency.data:
            query = query.join(Goal)
            if form.category.data:
                query = query.filter(Goal.goal_category == form.category.data)
            if form.frequency.data:
                query = query.filter(Goal.frequency == form.frequency.data)

        if form.city.data and form.city.data.strip():
            query = query.filter(User.city.ilike(f"%{form.city.data.strip()}%"))

        users = query.distinct().all()
        scored = [
            (u, match_score(current_user, u), Connection.between(current_user.id, u.id))
            for u in users
        ]
        # Primär nach Match-Score, bei Gleichstand nach Reputation (FA-13 AK3) —
        # der zuverlässigere Partner erscheint weiter oben.
        results = sorted(scored, key=lambda x: (x[1], x[0].reputation), reverse=True)

    return render_template("search.html", form=form, results=results, searched=searched)


@main_bp.route("/matches")
@login_required
def matches():
    """Top-3-Matches je eigenem Ziel (FA-05), separat von der gefilterten Suche."""
    matches_by_goal = [
        (
            goal,
            [
                (user, score, Connection.between(current_user.id, user.id))
                for user, score in top_matches_for_goal(goal)
            ],
        )
        for goal in current_user.goals
    ]
    return render_template("matches.html", matches_by_goal=matches_by_goal)


@main_bp.route("/connect/<int:user_id>", methods=["POST"])
@login_required
def send_connection(user_id):
    other = db.get_or_404(User, user_id)
    if other.id == current_user.id:
        abort(400)
    if Connection.between(current_user.id, other.id):
        flash("Es besteht bereits eine Verbindungsanfrage oder -partnerschaft.", "info")
        return redirect(url_for("main.user_profile", user_id=other.id))
    db.session.add(Connection(user1_id=current_user.id, user2_id=other.id, status="requested"))
    db.session.commit()
    # FA-10 AK1: E-Mail bei neuem passendem Partner (Verbindungsanfrage).
    notify(
        other,
        f"{current_user.name} möchte sich mit dir verbinden",
        f"Hi {other.name}, {current_user.name} hat dir auf GrindMate eine "
        "Verbindungsanfrage gesendet.",
    )
    flash(f"Verbindungsanfrage an {other.name} gesendet.", "success")
    return redirect(url_for("main.user_profile", user_id=other.id))


@main_bp.route("/connections/<int:conn_id>/accept", methods=["POST"])
@login_required
def accept_connection(conn_id):
    conn = db.get_or_404(Connection, conn_id)
    if conn.user2_id != current_user.id or conn.status != "requested":
        abort(403)
    conn.status = "active"
    db.session.commit()
    flash(f"Verbindung mit {conn.user1.name} ist jetzt aktiv!", "success")
    return redirect(url_for("main.profile"))


@main_bp.route("/connections/<int:conn_id>/decline", methods=["POST"])
@login_required
def decline_connection(conn_id):
    conn = db.get_or_404(Connection, conn_id)
    if current_user.id not in (conn.user1_id, conn.user2_id):
        abort(403)
    other_name = conn.user1.name if conn.user2_id == current_user.id else conn.user2.name
    db.session.delete(conn)
    db.session.commit()
    flash(f"Verbindungsanfrage mit {other_name} wurde zurückgezogen.", "info")
    return redirect(url_for("main.profile"))


@main_bp.route("/rate/<int:user_id>", methods=["POST"])
@login_required
def rate_user(user_id):
    """Einen aktiven Partner bewerten (FA-13 AK2). Re-Bewerten überschreibt."""
    other = db.get_or_404(User, user_id)
    conn = Connection.between(current_user.id, user_id)
    # Nur aktive Partner dürfen sich bewerten (NFA-03 / FA-13 AK2).
    if other.id == current_user.id or conn is None or conn.status != "active":
        abort(403)
    form = RatingForm()
    if form.validate_on_submit():
        stars = int(form.stars.data)
        rating = Rating.query.filter_by(rater_id=current_user.id, ratee_id=user_id).first()
        if rating:
            rating.stars = stars
        else:
            db.session.add(Rating(rater_id=current_user.id, ratee_id=user_id, stars=stars))
        db.session.commit()
        flash(f"Bewertung für {other.name} gespeichert.", "success")
    else:
        flash("Bewertung konnte nicht gespeichert werden.", "danger")
    return redirect(url_for("main.user_profile", user_id=user_id))


@main_bp.route("/checkin", methods=["POST"])
@login_required
def checkin():
    form = CheckinForm()
    form.goal.choices = _goal_choices(current_user)
    if not form.validate_on_submit():
        flash("Check-in konnte nicht gespeichert werden.", "danger")
        return redirect(url_for("main.grindprogress"))

    goal_id = int(form.goal.data) if form.goal.data else None
    today = date.today()
    already = Checkin.query.filter_by(
        user_id=current_user.id, checkin_date=today, goal_id=goal_id
    ).first()
    if already:
        flash("Für heute ist hier bereits ein Check-in erfasst.", "info")
        return redirect(url_for("main.grindprogress"))

    db.session.add(Checkin(
        user_id=current_user.id,
        goal_id=goal_id,
        checkin_date=today,
        note=(form.note.data.strip() or None) if form.note.data else None,
    ))
    db.session.commit()
    flash("Check-in erfasst – weiter so!", "success")
    return redirect(url_for("main.grindprogress"))


@main_bp.route("/chat/<int:conn_id>", methods=["GET", "POST"])
@login_required
def chat(conn_id):
    conn = db.get_or_404(Connection, conn_id)
    if not conn.involves(current_user.id):
        abort(403)  # NFA-03 / FA-07 AK3: only the two partners may read the chat
    if conn.status != "active":
        abort(404)  # FA-06 AK2: chat is unlocked only after a mutual match

    form = MessageForm()
    if form.validate_on_submit():
        db.session.add(Message(
            connection_id=conn.id,
            sender_id=current_user.id,
            text=form.text.data.strip(),
        ))
        db.session.commit()
        # FA-10 AK1: E-Mail an den Partner bei neuer Nachricht. Der Inhalt der
        # Nachricht wird bewusst nicht mitgeschickt (Datenschutz, NFA-03).
        partner = conn.partner_of(current_user)
        notify(
            partner,
            f"Neue Nachricht von {current_user.name}",
            f"Hi {partner.name}, du hast auf GrindMate eine neue Nachricht von "
            f"{current_user.name}.",
        )
        return redirect(url_for("main.chat", conn_id=conn.id))

    # FA-16 AK1: Beim Öffnen des Chats die Nachrichten des Partners als gelesen
    # markieren, damit der Absender den Lese-Status sieht.
    now = datetime.utcnow()
    unread = [m for m in conn.messages if m.sender_id != current_user.id and m.read_at is None]
    if unread:
        for m in unread:
            m.read_at = now
        db.session.commit()

    return render_template(
        "chat.html", conn=conn, partner=conn.partner_of(current_user), form=form,
    )


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Nutzereinstellungen — E-Mail-Notification an/aus (FA-10 AK2)."""
    form = SettingsForm()
    if form.validate_on_submit():
        current_user.notify_email = form.notify_email.data
        db.session.commit()
        flash("Einstellungen gespeichert.", "success")
        return redirect(url_for("main.settings"))
    if request.method == "GET":
        # Checkbox-Zustand für die Anzeige vorbelegen (nicht via obj, sonst
        # bleibt ein abgewähltes Häkchen beim POST auf dem alten Wert).
        form.notify_email.data = current_user.notify_email
    return render_template("settings.html", form=form)


_WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
# Grenzen für die Chat-Route (Abuse-/Kosten-Schutz und Datensparsamkeit).
_MAX_TURNS = 20
_MAX_MSG_LEN = 2000


def _longest_streak(dates: set) -> int:
    """Längster zusammenhängender Check-in-Lauf aller Zeiten (Tage)."""
    if not dates:
        return 0
    ordered = sorted(dates)
    longest = run = 1
    for prev, cur in zip(ordered, ordered[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)
    return longest


def _coach_facts(user):
    """Berechnete Fakten für den situativen Kopf-Satz (rein aus der DB)."""
    dates = {c.checkin_date for c in user.checkins}
    best_weekday = None
    if dates:
        counts = Counter(d.weekday() for d in dates)
        best_weekday = _WEEKDAYS_DE[counts.most_common(1)[0][0]]
    days_since = (date.today() - max(dates)).days if dates else None
    return {
        "streak": user.streak,
        "longest_streak": _longest_streak(dates),
        "quote": round(user.activity_level * 100),
        "checked_in": _checked_in_today(user),
        "best_weekday": best_weekday,
        "days_since_checkin": days_since,
    }


def _coach_context(user):
    """Kompakter, datensparsamer Nutzerkontext für die API (NFA-09)."""
    goal = user.goals[0] if user.goals else None
    return {
        "name": user.name.split()[0] if user.name else None,
        "goal": goal.goal_text if goal else None,
        "category": goal.goal_category if goal else None,
        "streak": user.streak,
        "quote": round(user.activity_level * 100),
        "checked_in": _checked_in_today(user),
    }


def _sanitize_chat(raw):
    """Konversationsverlauf aus dem Request säubern und validieren.

    Nur `user`/`assistant`-Rollen, gekürzte Inhalte, führende Assistant-
    Nachrichten entfernt, auf die letzten Turns begrenzt; die letzte Nachricht
    muss vom Nutzer stammen. Gibt [] zurück, wenn nichts Gültiges übrig bleibt.
    """
    if not isinstance(raw, list):
        return []
    cleaned = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        content = content.strip()[:_MAX_MSG_LEN]
        if not content:
            continue
        cleaned.append({"role": role, "content": content})
    # Führende Assistant-Nachrichten entfernen (API verlangt Start mit user).
    while cleaned and cleaned[0]["role"] == "assistant":
        cleaned.pop(0)
    cleaned = cleaned[-_MAX_TURNS:]
    if not cleaned or cleaned[-1]["role"] != "user":
        return []
    return cleaned


@main_bp.route("/coach")
@login_required
def coach():
    """KI-Coach-Seite: situativer Kopf-Satz, Chat-Coach und Vorschläge (FA-11)."""
    facts = _coach_facts(current_user)
    return render_template(
        "coach.html",
        facts=facts,
        headline=coach_headline(facts),
    )


@main_bp.route("/coach/message", methods=["POST"])
@login_required
def coach_message():
    """Chat-Endpunkt: nimmt den Verlauf als JSON, ergänzt serverseitig System-
    Prompt + Nutzerkontext und ruft die Anthropic-API auf (FA-11, NFA-09).

    Das Frontend spricht ausschliesslich mit dieser Route, nie direkt mit der
    externen API. Der API-Key bleibt serverseitig in der Umgebungsvariablen.
    """
    data = request.get_json(silent=True) or {}
    messages = _sanitize_chat(data.get("messages"))
    if not messages:
        return jsonify(error="Keine gültige Nachricht erhalten."), 400
    reply = chat_reply(messages, _coach_context(current_user))
    return jsonify(reply=reply)
