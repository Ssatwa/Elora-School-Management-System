from config.settings import production


def test_production_settings_enable_secure_transport():
    assert production.SESSION_COOKIE_SECURE is True
    assert production.CSRF_COOKIE_SECURE is True
    assert production.SECURE_SSL_REDIRECT is True
    assert production.SECURE_HSTS_SECONDS == 31_536_000
    assert (
        "django.middleware.clickjacking.XFrameOptionsMiddleware"
        in production.MIDDLEWARE
    )


def test_production_settings_disable_debug():
    assert production.DEBUG is False
