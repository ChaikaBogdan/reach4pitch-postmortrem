# Configuration samples

## Setup

- [systemd](https://github.com/systemd/systemd)
- [nginx](https://nginx.org/en/)
- [postgres v12](https://www.postgresql.org/)
- [poetry dot env plugin](https://pypi.org/project/poetry-dotenv-plugin/)

## Running commands

Prefix poetry invocation with location of .env file

```bash
PIPENV_DOTENV_LOCATION=../.env poetry run python manage.py loaddata db.json
```
