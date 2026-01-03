
from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent # old - 2 level top
BASE_DIR = Path(__file__).resolve().parent.parent.parent # new - 3 level top

import os
from dotenv import load_dotenv

load_dotenv()

from decouple import config
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import timedelta
from decouple import config



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

# Application definition
import sys
sys.path.append(str(BASE_DIR / 'apps'))

INSTALLED_APPS = [
    # static file
    'cloudinary',
    'cloudinary_storage',

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third Party
    'rest_framework',
    'rest_framework.authtoken', # Required by dj-rest-auth
    'rest_framework_simplejwt',
    # 'rest_framework_simplejwt.token_blacklist', # For logout to work properly
    
    'dj_rest_auth',
    'dj_rest_auth.registration',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', # Google Provider

    # 'debug_toolbar', # Only load Debug Toolbar if we are NOT testing
    
    # local apps
    "users",
    "workspace",
    "community",
    'notifications',
    'router',

]

AUTH_USER_MODEL = "users.User"

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://flowstack-gamma.vercel.app",
]


CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://flowstack-backend.onrender.com",
    "https://flowstack-gamma.vercel.app",
]


CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET')
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]



ROOT_URLCONF = "src.urls"
SITE_ID = 1
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # "rest_framework.authentication.TokenAuthentication",  # Basic static token auth
        # "rest_framework.authentication.SessionAuthentication",  # Django admin & templates
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # SPA & mobile apps
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',  # For guests (not logged in)
        'rest_framework.throttling.UserRateThrottle'   # For logged-in users
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',  # Guests get 10 requests per min
        'user': '1000/day',    # Users get 1000 requests per day
        'sensitive_action': '5/minute', # <--- NEW SCOPE
    }
}


SIMPLE_JWT = {
    # 'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True, # Important: Issue new refresh token on use
    'BLACKLIST_AFTER_ROTATION': True, # Important: Old refresh token becomes invalid
    'AUTH_HEADER_TYPES': ('Bearer',),
    "UPDATE_LAST_LOGIN": True,                       

}
REST_USE_JWT = True
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': None,          # <--- Must be explicitly None
    'JWT_AUTH_REFRESH_COOKIE': None,  # <--- Must be explicitly None
    'JWT_AUTH_HTTPONLY': False,       # Optional, but good to be explicit
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # keep this since you removed username field
ACCOUNT_EMAIL_VERIFICATION = "none"       # keep this if you don’t want verification
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_LOGIN_METHODS = {"email"}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "src.wsgi.application"




STORAGES = {
    # Media: Goes to Cloudinary
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    
    # Static: Stays local (or use WhiteNoise in production)
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
# MEDIA_URL = "media/"
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'  # This is always 'resend' for SMTP
EMAIL_HOST_PASSWORD = 're_123456789'  # Your actual Resend API Key
DEFAULT_FROM_EMAIL = 'onboarding@resend.dev'  # Or your verified domain


# CELERY SETTINGS
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

