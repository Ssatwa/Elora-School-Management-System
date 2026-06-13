# Production Readiness

## Release checks

Run the following before deployment:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\mypy.exe apps config
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe manage.py makemigrations --check
npm run css:build
.\.venv\Scripts\pip-audit.exe
```

Set production environment variables and run:

```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings.production"
$env:SECRET_KEY="<at-least-50-random-characters>"
$env:ALLOWED_HOSTS=".elora.co.ke"
.\.venv\Scripts\python.exe manage.py check --deploy
```

## Monitoring

- `/health/` confirms the web process is responding.
- `/ready/` confirms the database connection is available.
- Every response includes `X-Request-ID` for log correlation.
- Production logs are emitted as one JSON object per line.
- Celery jobs retain state and retry metadata in their domain job records.

## Backup rehearsal

Follow `docs/operations/backup-restore.md` before each release. Record the backup
timestamp, restore target, migration level, row counts, media verification, and
operator sign-off. Never rehearse against the production database.

## Deployment

Use the multi-stage Docker image as a non-root user. Apply migrations, collect
static files, verify `/ready/`, then shift traffic. Keep the previous image and
database backup available for rollback.
