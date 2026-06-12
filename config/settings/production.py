from .base import *  # noqa: F403

DEBUG = False
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa: F405
