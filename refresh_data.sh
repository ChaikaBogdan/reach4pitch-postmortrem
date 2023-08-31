#!/bin/bash
set -euo pipefail

poetry run python manage.py sqlflush | poetry run python manage.py dbshell
poetry run python manage.py loaddata db.json
poetry run python manage.py fixdata
