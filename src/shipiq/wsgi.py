"""WSGI entrypoint for gunicorn: ``gunicorn shipiq.wsgi:app``."""

from shipiq.api.app import create_app

app = create_app()
