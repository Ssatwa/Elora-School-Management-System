from .base import *  # noqa: F403

SECRET_KEY = "test-secret-key"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE  # noqa: F405
    if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
]
