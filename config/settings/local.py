from .base import *  # noqa: F403

DEBUG = True

if env.bool("LOCAL_USE_SQLITE", default=True):  # noqa: F405
    _sqlite_path = Path(  # noqa: F405
        env("LOCAL_SQLITE_PATH", default=str(BASE_DIR / "db.sqlite3"))  # noqa: F405
    )
    if not _sqlite_path.is_absolute():
        _sqlite_path = BASE_DIR / _sqlite_path  # noqa: F405
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_path,
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "elora-local",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
