from .common import *  # noqa: F403
from .common import BASE_DIR, env_list

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", *env_list("ALLOWED_HOSTS")]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
