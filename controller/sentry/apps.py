from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SentryConfig(AppConfig):
    name = "controller.sentry"
    verbose_name = _("sentry")
