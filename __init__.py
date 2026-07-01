"""Application factory for the Accountability-Partner app.

Extends the Dozenten-Starter (hello-world-fswd) pattern: this package's
__init__.py builds the Flask app via create_app(), main.py runs it.
"""
import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Liest .env im Projekt-Root (falls vorhanden) in os.environ ein, bevor die
# Config unten daraus gelesen wird. Ohne .env-Datei passiert einfach nichts.
load_dotenv()

# Extensions are created here (unbound) and bound to the app inside create_app.
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # SECRET_KEY is needed for sessions and CSRF protection (Flask-WTF).
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Default: SQLite file in the instance/ folder. Switch to MySQL later by
    # setting DATABASE_URL, e.g. mysql+pymysql://user:pass@localhost:3306/db
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "app.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Foto-Upload: lokales Verzeichnis, max. 5 MB
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # E-Mail-Notification (FA-10): optionales SMTP. Ohne MAIL_SERVER wird nur
    # geloggt, sodass die App ohne Mailserver lauffähig bleibt.
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "1") == "1"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_SENDER"] = os.environ.get("MAIL_SENDER", "noreply@momentum.local")

    # Bind extensions to this app.
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Bitte melde dich zuerst an."

    # Import models AFTER db exists to avoid circular imports.
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register controllers (blueprints).
    from .auth import auth_bp
    from .views import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Register the `flask seed` CLI command.
    from .seed import register_cli
    register_cli(app)

    # Create tables on startup if they don't exist yet.
    with app.app_context():
        db.create_all()

    return app
