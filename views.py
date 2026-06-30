"""Main controller: landing page, profile, goal management, search & connections."""
import os

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, abort, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import User, Goal, Photo, Connection, match_score
from .forms import EditProfileForm, GoalForm, SearchForm

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.profile"))
    return render_template("landing.html")


@main_bp.route("/profile")
@login_required
def profile():
    pending_requests = Connection.query.filter_by(
        user2_id=current_user.id, status="requested"
    ).all()
    return render_template("profile.html", user=current_user, pending_requests=pending_requests)


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
    return render_template("user_profile.html", user=user, connection=connection)


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
        results = sorted(scored, key=lambda x: x[1], reverse=True)

    return render_template("search.html", form=form, results=results, searched=searched)


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
