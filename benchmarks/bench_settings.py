"""Django settings used for every benchmarked build.

Imported as DJANGO_SETTINGS_MODULE=bench_settings with this directory on
PYTHONPATH, so every build (old DRF and Bolt) runs with DEBUG off, quiet
logging and its own SQLite database (BENCH_DB).
"""
import os

from inverter_project.settings.dev import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = ["*"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ["BENCH_DB"]}}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["null"], "level": "WARNING", "propagate": False},
        "django.server": {"handlers": ["null"], "level": "WARNING", "propagate": False},
    },
}
