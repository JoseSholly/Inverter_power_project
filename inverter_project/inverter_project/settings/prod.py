import dj_database_url
from decouple import config

from .common import *  # noqa: F403
from .common import BASE_DIR, env_list

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost", *env_list("ALLOWED_HOSTS")]

DATABASES = {
    'default': dj_database_url.parse(config("DATABASE_URL"), conn_max_age=600),
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

CORS_ALLOW_CREDENTIALS = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
