#!/bin/sh
set -e
PORT="${PORT:-8080}"
exec gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --threads 4 shipiq.wsgi:app
