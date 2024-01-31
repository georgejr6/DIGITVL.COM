import os
import datetime
from pathlib import Path

import stripe
from celery import Celery
from django.urls import reverse_lazy
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# OR, the same with increased verbosity
load_dotenv(verbose=True)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'fpixt*kq71@-#51!@l2m%%)(&#_=3t)f@^!2w_^-1k26wxt4z1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'accounts',
    'announcement',
    'advertisement',
    'beats',
    'blogs',
    'feeds',
    'taggit',
    'taggit_serializer',
    'userdata',
    'subscriptions',
    'donations',
    'support',
    'redeemCoins',
    'tweets',
    'invitation',
    'phonenumber_field',
    'notifications',
    'linktree',
    'xrpwallet',
    'rest_framework.authtoken',
    'rest_auth',
    'django.contrib.sites',
    'sortedm2m',
    'easy_thumbnails',
    'django_cleanup.apps.CleanupConfig',
    'django_extensions',
    'debug_toolbar',
    'import_export',
    'django_celery_beat',
    "djstripe",
    'rest_framework_simplejwt',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]
# INTERNAL_IPS = [
#     # ...
#     '127.0.0.1',
#     # ...
# ]

# Custom Model
AUTH_USER_MODEL = 'accounts.User'

ROOT_URLCONF = 'marketplace.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, 'templates']
        ,
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

WSGI_APPLICATION = 'marketplace.wsgi.application'

# CORS SETTINGS
CORS_ORIGIN_ALLOW_ALL = True
#
# CORS_ORIGIN_WHITELIST = [
#     "http://localhost:3000",
#
#     "http://127.0.0.1:8000"
# ]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Session
CART_SESSION_ID = 'cart'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# rest framework settings
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'NON_FIELD_ERRORS_KEY': 'errors',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [

        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10

}
# jwt
# JWT_AUTH = {
#     'JWT_RESPONSE_PAYLOAD_HANDLER': 'marketplace.utils.my_jwt_response_handler',
#     'JWT_EXPIRATION_DELTA': datetime.timedelta(days=3),
#     'JWT_ALLOW_REFRESH': True,
#     'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
# }
SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('jwt',),
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=5),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=6),

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_OBTAIN_SERIALIZER": "accounts.serializers.CustomTokenObtainPairSerializer",

}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'novam_music',
        'USER': 'dbadmin',
        'PASSWORD': 'abc123!',
        'HOST': 'localhost',
        # 'PORT': '25060',

    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

# is equal to os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# Media Folder settings
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# # Redis Support

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

PHONENUMBER_DEFAULT_REGION = "US"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD =  os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL =  os.getenv('DEFAULT_FROM_EMAIL')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


DOMAIN_URL = os.getenv('DOMAIN_URL')

# for cache timeline
CACHE_TTL = 60 * 5
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BROKER", "redis://localhost:6379/0")
# If time zones are active (USE_TZ = True) define your local CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_TIMEZONE = 'America/New_York'

# Let's make things happen
CELERY_BEAT_SCHEDULE = {

    # Executes every Friday at 4pm
    'send_email_to_non_verify_account': {
        'task': 'accounts.tasks.send_email_to_non_verify_account',
        'schedule': crontab(hour=12, minute=30),
    },
}

# santry setting for production error handle


# Stripe setting
stripe.api_version = '2020-08-27'
STRIPE_TEST_SECRET_KEY =  os.environ.get('STRIPE_TEST_SECRET_KEY')
STRIPE_LIVE_MODE = False  # Change to True in production
DJSTRIPE_WEBHOOK_SECRET = "whsec_xxx"
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

try:
    from .local_settings import *
except ImportError:
    pass
