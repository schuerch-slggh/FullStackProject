"""Main controller: home + personal profile."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.profile"))
    return redirect(url_for("auth.login"))


@main_bp.route("/profile")
@login_required
def profile():
    # current_user is the logged-in User entity, loaded from the DB.
    return render_template("profile.html", user=current_user)
