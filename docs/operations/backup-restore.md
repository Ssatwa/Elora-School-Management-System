# Backup And Restore

## Backup

Create a PostgreSQL custom-format backup and separately copy media storage:

```powershell
docker compose exec db pg_dump -U elora -d elora -Fc -f /tmp/elora.dump
docker compose cp db:/tmp/elora.dump .\backups\elora.dump
```

Back up the `media_data` volume or the configured S3-compatible bucket using
the storage provider's versioned backup process. Keep database and media backup
timestamps together.

## Restore Rehearsal

1. Create an empty restore database.
2. Restore with `pg_restore --clean --if-exists`.
3. Restore the matching media snapshot.
4. Run `python manage.py migrate`.
5. Run readiness, login, tenant-isolation, and report-download smoke tests.
6. Record restore duration, failures, and the verified recovery point.

Never overwrite the production database to test a restore.
