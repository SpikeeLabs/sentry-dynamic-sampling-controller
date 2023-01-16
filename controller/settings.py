"""
Django settings for controller project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("ENV", "production") != "production"
TESTING = sys.argv[1:2] == ["test"] or os.getenv("TESTING")
ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "admin_action_tools",
    "django.contrib.admin",
    "django.contrib.auth",
    "mozilla_django_oidc",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_object_actions",
    "rest_framework",
    "widget_tweaks",
    "django_better_admin_arrayfield",
    "django_json_widget",
    "durationwidget",
    "controller.sentry",
]

AUTHENTICATION_BACKENDS = (
    # "django.contrib.auth.backends.ModelBackend",
    "controller.sentry.auth.ControllerOIDCAuthenticationBackend",
)

OIDC_RP_CLIENT_ID = os.getenv("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_RP_CLIENT_SECRET")
# "<URL of the OIDC OP authorization endpoint>"
OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv("OIDC_OP_AUTHORIZATION_ENDPOINT")
# "<URL of the OIDC OP token endpoint>"
OIDC_OP_TOKEN_ENDPOINT = os.getenv("OIDC_OP_TOKEN_ENDPOINT")
# "<URL of the OIDC OP userinfo endpoint>"
OIDC_OP_USER_ENDPOINT = os.getenv("OIDC_OP_USER_ENDPOINT")
# "<URL path to redirect to after login>"
LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL")
# "<URL path to redirect to after logout>"
LOGOUT_REDIRECT_URL = os.getenv("LOGOUT_REDIRECT_URL")

OIDC_RP_SIGN_ALGO = os.getenv("OIDC_RP_SIGN_ALGO", "RS256")

OIDC_OP_JWKS_ENDPOINT = os.getenv("OIDC_OP_JWKS_ENDPOINT")


DEVELOPER_GROUP = os.getenv("DEVELOPER_GROUP", "Developer")


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "controller.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "controller.sentry.utils.is_panic_activated",
            ],
        },
    },
]

WSGI_APPLICATION = "controller.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "sentry_backend"),
        "USER": os.getenv("POSTGRES_USER", "sentry_backend"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "sentry_backend"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CONN_MAX_AGE = None
APP_CACHE_TIMEOUT = 0

if not TESTING:
    APP_CACHE_TIMEOUT = int(os.getenv("APP_CACHE_TIMEOUT", "600"))
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.getenv("CACHE_REDIS_URL", "redis://127.0.0.1:6379"),
            "OPTIONS": {
                "parser_class": "redis.connection.PythonParser",
                "pool_class": "redis.BlockingConnectionPool",
            },
            "TIMEOUT": int(os.getenv("CACHE_TIMEOUT", "120")),
        }
    }


DEFAULT_SAMPLE_RATE = float(os.getenv("DEFAULT_SAMPLE_RATE", "0.1"))
DEFAULT_WSGI_IGNORE_PATHS = os.getenv("DEFAULT_WSGI_IGNORE_PATHS", "/health,/healthz,/health/,/healthz/").split(",")


DEFAULT_CELERY_IGNORE_TASKS = []


CACHE_META_INVALIDATION = {
    "SERVER_NAME": os.getenv("CACHE_META_SERVER_NAME", "localhost"),
    "SERVER_PORT": int(os.getenv("CACHE_META_SERVER_PORT", "8000")),
    "HTTP_ACCEPT": os.getenv("CACHE_META_HTTP_ACCEPT", "*/*"),
}


MAX_BUMP_TIME_SEC = int(os.getenv("MAX_BUMP_TIME_SEC", "0"))
if MAX_BUMP_TIME_SEC == 0:
    MAX_BUMP_TIME_SEC = 30 * 60  # 30 minutes

PANIC_KEY = "PANIC"
