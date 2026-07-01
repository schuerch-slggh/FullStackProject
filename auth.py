"""Auth controller (login / logout / register)."""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from . import db
from .models import User, Goal, Photo
from .forms import LoginForm, RegistrationForm, compose_frequency

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.grindprogress"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.grindprogress"))
        flash("E-Mail oder Passwort ist falsch.", "danger")
    return render_template("login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.grindprogress"))
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User(
            email=email,
            name=form.name.data.strip(),
            age=form.age.data,
            city=form.city.data,
            bio=form.bio.data,
        )
        user.set_password(form.password.data)
        user.photos.append(Photo(
            url=f"https://i.pravatar.cc/300?u={email}",
            is_primary=True,
        ))
        user.goals.append(Goal(
            goal_category=form.goal_category.data,
            goal_text=form.goal_text.data,
            frequency=compose_frequency(form.frequency_count.data, form.frequency_unit.data),
            preferred_checkin_time=(
                form.preferred_checkin_time.data.strftime("%H:%M")
                if form.preferred_checkin_time.data else None
            ),
        ))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Willkommen bei GrindMate! Dein Profil ist angelegt.", "success")
        return redirect(url_for("main.grindprogress"))
    return render_template("register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
