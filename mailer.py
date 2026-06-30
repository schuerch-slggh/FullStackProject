"""E-Mail-Notification (FA-10).

Echtes SMTP wird genutzt, wenn `MAIL_SERVER` konfiguriert ist; ohne Server wird
nur geloggt (Dev), damit die App nie von einem Mailserver abhängt. Unter
`TESTING` landet die Nachricht in einer In-Memory-Outbox für Assertions.
"""
import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to: str, subject: str, body: str) -> bool:
    """Verschickt eine E-Mail. True bei Versand/Erfassung, False bei reinem Log."""
    app = current_app
    if app.config.get("TESTING"):
        app.config.setdefault("EMAIL_OUTBOX", []).append(
            {"to": to, "subject": subject, "body": body}
        )
        return True

    server = app.config.get("MAIL_SERVER")
    if not server:
        app.logger.info("E-Mail (kein MAIL_SERVER, nur Log) an %s: %s", to, subject)
        return False

    msg = EmailMessage()
    msg["From"] = app.config.get("MAIL_SENDER", "noreply@momentum.local")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(server, app.config.get("MAIL_PORT", 587)) as smtp:
        if app.config.get("MAIL_USE_TLS", True):
            smtp.starttls()
        username = app.config.get("MAIL_USERNAME")
        password = app.config.get("MAIL_PASSWORD")
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)
    return True


def notify(user, subject: str, body: str) -> bool:
    """Benachrichtigt einen Nutzer, respektiert dessen Opt-out (FA-10 AK2)."""
    if not getattr(user, "notify_email", False) or not user.email:
        return False
    return send_email(user.email, subject, body)
