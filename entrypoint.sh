#!/bin/sh
set -e
python -m app.prepare
exec gunicorn --bind 0.0.0.0:3000 --workers 2 --access-logfile - --error-logfile - wsgi:app
