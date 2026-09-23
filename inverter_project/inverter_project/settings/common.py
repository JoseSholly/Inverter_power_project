"""
Settings shared by every environment. Environment-specific values live in
dev.py and prod.py; secrets and hosts come from environment variables or a
.env file (read by python-decouple).
"""

from pathlib import Path

from decouple import Csv, config

# Outer project directory (the one containing manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")


def env_list(name: str, default: str = "") -> list[str]:
    """Comma-separated env var -> list, ignoring blank entries."""
    return [value for value in config(name, default=default, cast=Csv()) if value]


INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bolt',

    # apps
    "power_calculator",
    "inverter_rating_v2",
    "api",
]

# django-bolt API instance served by `manage.py runbolt`
BOLT_API = ["inverter_project.api:api"]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inverter_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'inverter_project.wsgi.application'
ASGI_APPLICATION = 'inverter_project.asgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache. Local memory by default; prod.py switches to Redis when REDIS_URL is set
# (a shared cache is needed for invalidation to reach every server process).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "inverter-default",
    }
}
APPLIANCE_CACHE_TIMEOUT = config("APPLIANCE_CACHE_TIMEOUT", default=3600, cast=int)
"""Seconds a cached appliance catalogue lives; a safety net, since changes invalidate it."""

# Isolates tests from each other's cache entries (see inverter_project/test_runner.py).
TEST_RUNNER = "inverter_project.test_runner.CacheIsolatingTestRunner"

# CORS for the API. django-bolt reads these settings directly.
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
