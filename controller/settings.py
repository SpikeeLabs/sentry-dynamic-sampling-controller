"""Django settings for controller project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
import sys
from pathlib import Path
from urllib.parse import quote

import sentry_sdk
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("ENV", "production") != "production"
TESTING = sys.argv[1:2] == ["test"] or os.getenv("TESTING")

# Static and Media
STATIC_URL = os.getenv("STATIC_URL", "/assets/static/")
MEDIA_URL = os.getenv("MEDIA_URL", "/assets/media/")
STATIC_ROOT = os.path.join(BASE_DIR, "assets/static")
MEDIA_ROOT = os.path.join(BASE_DIR, "assets/media")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "vendor/"),)

VENDOR = {
    "chartjs": {
        "url": "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/",
        "js": [
            {
                "path": "chart.min.js",
                "sri": "sha384-9MhbyIRcBVQiiC7FSd7T38oJNj2Zh+EfxS7/vjhBi4OOT78NlHSnzM31EZRWR1LZ",
            }
        ],
    },
    "chartjs-date": {
        "url": "https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/",
        "js": [
            {
                "path": "chartjs-adapter-date-fns.bundle.min.js",
                "sri": "sha384-cVMg8E3QFwTvGCDuK+ET4PD341jF3W8nO1auiXfuZNQkzbUUiBGLsIQUE+b1mxws",
            }
        ],
    },
    "chartjs-zoom": {
        "url": "https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.0/dist/",
        "js": [
            {
                "path": "chartjs-plugin-zoom.min.js",
                "sri": "sha384-AC/SQgflSDa6sFR0rk5chlHjSLMS9fHmSE50vY7uoBiqrCWtDUXoOBCKaoQQFBrl",
            }
        ],
    },
    "hammerjs": {
        "url": "https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/",
        "js": [
            {
                "path": "hammer.min.js",
                "sri": "sha384-Cs3dgUx6+jDxxuqHvVH8Onpyj2LF1gKZurLDlhqzuJmUqVYMJ0THTWpxK5Z086Zm",
            }
        ],
    },
}


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

if os.getenv("CSRF_TRUSTED_ORIGINS", ""):
    CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

if DEBUG:
    ALLOWED_HOSTS = ["*"]

# Application definition
# URLs
ROOT_URLCONF = "controller.urls"

# Application definition
# URLs
ROOT_URLCONF = "controller.urls"

# WSGI
WSGI_APPLICATION = "controller.wsgi.application"

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
    "health_check",
    "health_check.db",  # stock Django health checkers
    "health_check.cache",
    "vendor_files",
    "controller.sentry",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# template
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "controller" / "sentry" / "templates"],
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

# Authentication
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

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Reuse db connection
CONN_MAX_AGE = None

# CACHE
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


# App config
DEFAULT_SAMPLE_RATE = float(os.getenv("DEFAULT_SAMPLE_RATE", "0.1"))

DEFAULT_WSGI_IGNORE_PATHS = os.getenv("DEFAULT_WSGI_IGNORE_PATHS", "/health,/healthz,/health/,/healthz/").split(",")

DEFAULT_WSGI_IGNORE_USER_AGENT = os.getenv("DEFAULT_WSGI_IGNORE_USER_AGENT", "kube-probe/").split(",")


DEFAULT_CELERY_IGNORE_TASKS = []

CACHE_META_INVALIDATION = {
    "SERVER_NAME": os.getenv("CACHE_META_SERVER_NAME", "localhost"),
    "SERVER_PORT": int(os.getenv("CACHE_META_SERVER_PORT", "8000")),
    "HTTP_ACCEPT": os.getenv("CACHE_META_HTTP_ACCEPT", "*/*"),
}

MAX_BUMP_TIME_SEC = int(os.getenv("MAX_BUMP_TIME_SEC", "0"))
if MAX_BUMP_TIME_SEC == 0:
    MAX_BUMP_TIME_SEC = 30 * 60  # 30 minutes

# CACHE KEY for panic
PANIC_KEY = "PANIC"

DEVELOPER_GROUP = os.getenv("DEVELOPER_GROUP", "Developer")
DEVELOPER_ACTIONS = ["bump_sample_rate_app", "enable_disable_metrics_app"]

APP_AUTO_PRUNE = os.getenv("APP_AUTO_PRUNE", "true").lower() == "true"
APP_AUTO_PRUNE_MAX_AGE_DAY = int(os.getenv("APP_AUTO_PRUNE_MAX_AGE_DAY", "30"))

EVENT_AUTO_PRUNE = os.getenv("EVENT_AUTO_PRUNE", "true").lower() == "true"
EVENT_AUTO_PRUNE_MAX_AGE_DAY = int(os.getenv("EVENT_AUTO_PRUNE_MAX_AGE_DAY", "30"))


# Celery
BROKER_USER = quote(os.environ.get("CELERY_BROKER_USER", "rabbitmq"))
BROKER_PASSWORD = quote(os.environ.get("CELERY_BROKER_PASSWORD", "rabbitmq"))
BROKER_HOST = os.environ.get("CELERY_BROKER_HOST", "localhost")
BROKER_PORT = os.environ.get("CELERY_BROKER_PORT", "5672")
BROKER_VHOST = quote(os.environ.get("CELERY_BROKER_VHOST", "/"))


CELERY_ACCEPT_CONTENT = ["json"]
CELERY_ACKS_LATE = True
CELERY_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_URL = f"amqp://{BROKER_USER}:{BROKER_PASSWORD}@{BROKER_HOST}:{BROKER_PORT}/{BROKER_VHOST}"

CELERY_BEAT_SCHEDULE = {
    "close-window": {
        "task": "controller.sentry.tasks.close_window",
        "schedule": crontab(),  # every minutes
    },
    "sentry-project-slug": {
        "task": "controller.sentry.tasks.pull_sentry_project_slug",
        "schedule": crontab(),  # every minutes
    },
    "populate-app": {
        "task": "controller.sentry.tasks.populate_app",
        "schedule": crontab(),  # every minutes
    },
    "monitor-sentry-usage": {
        "task": "controller.sentry.tasks.monitor_sentry_usage",
        "schedule": crontab(minute="1", hour="*"),  # every hour at minute 1
    },
}

if APP_AUTO_PRUNE:
    CELERY_BEAT_SCHEDULE["prune-inactive-app"] = {
        "task": "controller.sentry.tasks.prune_inactive_app",
        "schedule": crontab(minute="0", hour="*"),  # every hour
    }

if EVENT_AUTO_PRUNE:
    CELERY_BEAT_SCHEDULE["prune-old-event"] = {
        "task": "controller.sentry.tasks.prune_old_event",
        "schedule": crontab(minute="0", hour="*"),  # every hour
    }


SENTRY_API_TOKEN = os.getenv("SENTRY_API_TOKEN", "TEST")
SENTRY_ORGANIZATION_SLUG = os.getenv("SENTRY_ORGANIZATION_SLUG")
SENTRY_STATS_PERIOD = os.getenv("SENTRY_STATS_PERIOD", "30d")

DEFAULT_SPIKE_DETECTION_PARAM = {
    "lag": int(os.getenv("SPIKE_DETECTION_LAG", "48")),
    "threshold": int(os.getenv("SPIKE_DETECTION_THRESHOLD", "5")),
    "influence": float(os.getenv("SPIKE_DETECTION_INFLUENCE", "0.01")),
    "floor": int(os.getenv("SPIKE_DETECTION_FLOOR", "50")),
}


SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    from sentry_dynamic_sampling_lib import init_wrapper

    ENVIRONMENT = os.getenv("ENV", "production")
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
    )

    # hook sentry_dynamic_sampling_lib into sentry
    init_wrapper()


# Graph
DEFAULT_GRAPH_OPTION = {
    "aspectRatio": 4,
    "scales": {
        "xAxis": {"type": "timeseries"},
        "series": {"position": "left", "min": 0},
        "signal": {"position": "right", "min": 0, "max": 2},
    },
    "plugins": {
        "legend": {"position": "bottom"},
        "title": {"display": True, "text": "Detection Result"},
        "zoom": {
            "zoom": {
                "wheel": {"enabled": True, "modifierKey": "ctrl"},
                "pinch": {"enabled": True},
                "mode": "x",
            },
            "limits": {"xAxis": {"min": "original", "max": "original"}},
            "pan": {"enabled": True, "mode": "x", "modifierKey": "ctrl"},
        },
    },
    "elements": {"line": {"stepped": True}, "point": {"radius": 0}},
    "interaction": {"mode": "index", "intersect": False},
}
