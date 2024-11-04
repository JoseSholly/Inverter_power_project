from .common import *


SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG= False

ALLOWED_HOSTS=['127.0.0.1', 'localhost']

allowed_host_value= os.getenv("ALLOWED_HOSTS")

if allowed_host_value:
    ALLOWED_HOSTS.append(allowed_host_value)


database_url= os.getenv("DATABASE_URL")
DATABASES["default"] = dj_database_url.parse(database_url)

 
CSRF_TRUSTED_ORIGINS= os.getenv("CSRF_TRUSTED_ORIGINS").split(",")

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

    WHITENOISE_AUTOREFRESH = True
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_COMPRESS = True
    WHITENOISE_MANIFEST_STRICT = True 


CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(",")

CORS_ALLOW_CREDENTIALS = True 

SESSION_COOKIE_SECURE= True

CSRF_COOKIE_SECURE= True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',  # Change the path as needed
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}