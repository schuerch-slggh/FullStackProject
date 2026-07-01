try:
    # Läuft unter `flask --app main run`: main.py ist Teil des Root-Package.
    from . import create_app
except ImportError:
    # Läuft unter direktem Modul-Import (z.B. `gunicorn main:app`): main.py
    # hat dann kein Parent-Package, relative Imports funktionieren nicht.
    from __init__ import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
