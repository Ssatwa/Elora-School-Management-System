# Native Windows Development

Elora can run locally without Docker, PostgreSQL, Redis, or Linux
virtualization. This profile is intended for development and demonstrations;
production keeps PostgreSQL, Redis, and separate Celery workers.

## Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
npm install
npm run css:build
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://green-hills.localhost:8000/accounts/login/`.

Local settings use:

- SQLite at `db.sqlite3`
- Django's process-local memory cache
- Celery eager mode with in-memory broker and result backend
- Console email output

Tasks invoked with `.delay()` execute immediately in the web process. This is
useful for development but does not reproduce worker concurrency.

## Optional Native PostgreSQL

Install PostgreSQL for Windows, create an Elora database and user, then update
`.env`:

```dotenv
LOCAL_USE_SQLITE=False
DATABASE_URL=postgres://elora:your-password@localhost:5432/elora
```

Run migrations again after switching databases. PostgreSQL is required to
exercise row-level-security policies; the SQLite profile tests application
tenant scoping but cannot enforce PostgreSQL RLS.

## Production Difference

Use `config.settings.production` in deployed environments. Production requires
PostgreSQL and strong environment-provided secrets. Redis-backed Celery workers
and the scheduler should run as separate services.
