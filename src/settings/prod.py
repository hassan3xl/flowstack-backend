from .base import *
import os
import dj_database_url

DEBUG = False

SECRET_KEY = os.environ["SECRET_KEY"]

# ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")
DJANGO_ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "vercel.app",
    "flowstack-backend.onrender.com",
    "flowstack-gamma.vercel.app",
]

DATABASES = {

    "default": dj_database_url.config(default=os.getenv("NEON_DB"))
}

# Free-tier friendly cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

STATIC_ROOT = BASE_DIR / "staticfiles"

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
