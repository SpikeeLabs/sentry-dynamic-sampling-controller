"""All the choices."""
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class MetricType(TextChoices):
    """This enum is for the metric types.

    Attributes:
        WSGI (str): type for all app using a wsgi
        CELERY (str): type for all app celery worker
    """

    WSGI = "WSGI", _("WSGI")
    CELERY = "CELERY", _("CELERY")


class EventType(TextChoices):
    """This enum is for the event types.

    Attributes:
        FIRING (str): Mark the start of a new event
        DISCARD (str): Mark the end of an event

    """

    FIRING = "FIRING", _("firing")
    DISCARD = "DISCARD", _("discard")
