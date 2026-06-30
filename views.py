"""Main controller: landing page, personal profile, public profile view."""
import os

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import User
from .forms import EditProfileForm

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.profile"))
    return render_template("landing.html")


@main_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.age = form.age.data
        current_user.city = form.city.data
        current_user.goal_category = form.goal_category.data
        current_user.goal_text = form.goal_text.data
        current_user.frequency = form.frequency.data
        current_user.preferred_checkin_time = form.preferred_checkin_time.data
        current_user.bio = form.bio.data

        photo_file = form.photo.data
        if photo_file and photo_file.filename:
            filename = secure_filename(f"{current_user.id}_{photo_file.filename}")
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            photo_file.save(upload_path)
            current_user.photo_url = url_for("static", filename=f"uploads/{filename}")

        db.session.commit()
        flash("Profil gespeichert.", "success")
        return redirect(url_for("main.profile"))

    return render_template("edit_profile.html", form=form)


@main_bp.route("/u/<int:user_id>")
@login_required
def user_profile(user_id):
    user = db.get_or_404(User, user_id)
    return render_template("user_profile.html", user=user)
