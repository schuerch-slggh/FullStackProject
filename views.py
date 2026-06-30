"""Main controller: landing page + personal profile."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    # Eingeloggt -> direkt zum Profil; sonst die Startseite zeigen.
    if current_user.is_authenticated:
        return redirect(url_for("main.profile"))
    return render_template("landing.html")


@main_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)
