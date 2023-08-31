[![Django CI](https://github.com/ChaikaBogdan/reach4pitch/actions/workflows/django.yml/badge.svg?branch=main)](https://github.com/ChaikaBogdan/reach4pitch/actions/workflows/django.yml)
[![Deploy Release Tag to VPS](https://github.com/ChaikaBogdan/reach4pitch/actions/workflows/deploy.yml/badge.svg)](https://github.com/ChaikaBogdan/reach4pitch/actions/workflows/deploy.yml)
# Reach4Pitch


https://github.com/ChaikaBogdan/reach4pitch-postmortrem/assets/16524061/639b77e1-a6e9-413f-9c1c-bf456a630721


## Setup

- Install [poetry](https://python-poetry.org/)
- Install [redis](https://redis.io/)
- Git 2.22+ required for `poetry run pre-commit autoupdate` (it's using Partial clone feature)

```bash
./bootstrap.sh
```

## Development

```bash
poetry run python manage.py rqworker default # you will this for all delayed actions like sending emails
poetry run python manage.py makemigrations
poetry run python manage.py migrate
poetry run python manage.py test
poetry run python manage.py dumpdata --exclude django_rq --exclude captcha --exclude auth --exclude contenttypes --exclude sessions --exclude admin --indent 4 > db.json
poetry run djhtml .
poetry run pre-commit run --all-files
```
