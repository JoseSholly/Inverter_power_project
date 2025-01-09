from .common import *

DEBUG = True

ALLOWED_HOSTS = []

SECRET_KEY = os.getenv("SECRET_KEY")

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRESQL_DB_NAME"),
        "USER": os.getenv("POSTGRESQL_DB_USER"),
        "PASSWORD": os.getenv("POSTGRESQL_DB_PASSWORD"),
        "HOST": os.getenv("POSTGRESQL_DB_HOST", "localhost"),
        "PORT": os.getenv("POSTGRESQL_DB_PORT", "5432"),
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }
# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
