#!/bin/bash
set -eu
test -f db.sqlite3 && rm db.sqlite3
find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

poetry install
poetry run pre-commit install
poetry run pre-commit autoupdate
poetry run python manage.py migrate
poetry run python manage.py loaddata db.json
poetry run python manage.py runserver
