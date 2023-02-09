from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class MetricType(TextChoices):
    WSGI = "WSGI", _("WSGI")
    CELERY = "CELERY", _("CELERY")


class EventType(TextChoices):
    FIRING = "FIRING", _("firing")
    DISCARD = "DISCARD", _("discard")
