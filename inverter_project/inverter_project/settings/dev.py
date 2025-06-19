from .common import *

DEBUG = True

ALLOWED_HOSTS = []

SECRET_KEY = os.getenv("SECRET_KEY")

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
