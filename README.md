# Elora School Management System

Elora is a multi-school Django platform for Kenyan competency-based education.
It uses school subdomains, school-scoped memberships, role dashboards, and
defense-in-depth PostgreSQL tenant isolation.

## Requirements

- Python 3.13
- Node.js 24
- Git
- Docker Desktop is optional and requires hardware virtualization

## Native Windows Setup

This is the recommended development path when Docker Desktop is unavailable.
It uses SQLite, Django's in-memory cache, and eager Celery tasks, so PostgreSQL,
Redis, and a separate Celery worker are not required locally.

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
School demo accounts use `<role>@green-hills.localhost` and password
`EloraDemo123!`. The platform account is `super_admin@elora.local`.
The same role accounts are available for Sunrise Academy at
`<role>@sunrise.localhost`.

Milestone 2 review pages:

- `http://green-hills.localhost:8000/academics/`
- `http://green-hills.localhost:8000/staff/`
- `http://green-hills.localhost:8000/learners/`
- `http://green-hills.localhost:8000/learners/admit/`

To develop against a native PostgreSQL installation, set
`LOCAL_USE_SQLITE=False` and provide `DATABASE_URL` in `.env`. Redis and Celery
workers remain optional in local settings; staging and production use the full
service stack.

## Docker Setup

On a virtualization-capable machine, start Docker Desktop and run:

```powershell
Copy-Item .env.docker.example .env
docker compose up --build
```

The web entrypoint applies migrations and collects static files. PostgreSQL and
media data use named volumes.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe manage.py makemigrations --check
npm run css:build
```

Docker configuration can still be validated without starting containers:

```powershell
docker compose --env-file .env.docker.example config
```

Production settings verification uses:

```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings.production"
$env:SECRET_KEY="replace-with-a-secret"
$env:ALLOWED_HOSTS=".elora.co.ke"
.\.venv\Scripts\python.exe manage.py check --deploy
```

## Tenant Model

Each school has one or more `SchoolDomain` records. Tenant middleware resolves
the request host, attaches the active school, and sets PostgreSQL session
context. Every tenant-owned query must use explicit school scoping. School
memberships carry one or more stable role codes.

## Project Documentation

- Platform design: `docs/superpowers/specs/2026-06-12-elora-platform-design.md`
- Delivery roadmap: `docs/superpowers/plans/2026-06-12-elora-implementation-roadmap.md`
- School provisioning: `docs/operations/school-provisioning.md`
- Backup and restore: `docs/operations/backup-restore.md`
- Native Windows development: `docs/operations/native-windows-development.md`
- People and academic operations: `docs/operations/people-academics.md`
