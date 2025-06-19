from .common import *
from decouple import config
import os

DEBUG = True

ALLOWED_HOSTS = []

SECRET_KEY = config("SECRET_KEY", cast=str)

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
