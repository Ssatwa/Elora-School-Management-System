from pathlib import Path

from config.settings import local


def test_local_settings_use_sqlite_by_default() -> None:
    assert local.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert isinstance(local.DATABASES["default"]["NAME"], Path)


def test_local_settings_do_not_require_external_services() -> None:
    assert local.CACHES["default"]["BACKEND"] == ("django.core.cache.backends.locmem.LocMemCache")
    assert local.CELERY_TASK_ALWAYS_EAGER is True
    assert local.CELERY_TASK_EAGER_PROPAGATES is True
    assert local.CELERY_BROKER_URL == "memory://"
    assert local.CELERY_RESULT_BACKEND == "cache+memory://"
