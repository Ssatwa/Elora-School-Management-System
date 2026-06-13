# Elora School Management System

Elora is a multi-school Django platform for Kenyan competency-based education.
It uses school subdomains, school-scoped memberships, role dashboards, and
defense-in-depth PostgreSQL tenant isolation.

## Requirements

- Python 3.13
- Node.js 24
- Docker Desktop
- Git

## Local Setup

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

## Docker Setup

Start Docker Desktop, then run:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The web entrypoint applies migrations and collects static files. PostgreSQL and
media data use named volumes.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe manage.py makemigrations --check
npm run css:build
docker compose config
```

Production verification uses:

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
