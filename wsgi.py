"""WSGI-Einstiegspunkt für Prod-Server wie Gunicorn (`gunicorn wsgi:app`).

Die Module dieses Projekts (auth.py, views.py, models.py, ...) nutzen relative
Imports wie `from . import db`, weil das Projektverzeichnis selbst als Package
behandelt wird (Root-`__init__.py`). Unter `flask --app main run` löst Flask
das automatisch anhand des Ordnernamens auf; ein direkter Modul-Import durch
Gunicorn tut das nicht (main.py hätte dann kein Parent-Package). Deshalb
fügen wir hier das Eltern-Verzeichnis zum sys.path hinzu und importieren das
Projektverzeichnis unter seinem tatsächlichen Ordnernamen als Package — genau
das, was Flasks CLI intern macht.
"""
import importlib
import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_PROJECT_DIR)
_PACKAGE_NAME = os.path.basename(_PROJECT_DIR)

if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

app = importlib.import_module(_PACKAGE_NAME).create_app()
