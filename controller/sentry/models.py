from functools import partial
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_better_admin_arrayfield.models.fields import ArrayField

from controller.sentry.choices import EventType, MetricType
from controller.sentry.metrics import celery_merger, wsgi_merger


def settings_default_value(key):
    return getattr(settings, key)


MERGER = {MetricType.WSGI: wsgi_merger, MetricType.CELERY: celery_merger}


class Project(models.Model):
    """Project"""

    sentry_id = models.CharField(primary_key=True, max_length=50)
    sentry_project_slug = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    detection_param = models.JSONField(default=partial(settings_default_value, "DEFAULT_SPIKE_DETECTION_PARAM"))

    def __str__(self) -> str:
        return f"Project({self.sentry_id} - {self.sentry_project_slug if self.sentry_project_slug else 'Pending'})"


class Event(models.Model):
    """Event"""

    reference = models.UUIDField(primary_key=True, default=uuid4)
    type = models.CharField(choices=EventType.choices, max_length=10)
    timestamp = models.DateTimeField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="events")

    class Meta:
        ordering = ["timestamp"]


class App(models.Model):
    """App"""

    reference = models.CharField(primary_key=True, max_length=256)

    last_seen = models.DateTimeField(null=True, blank=True)
    default_sample_rate = models.FloatField(default=settings.DEFAULT_SAMPLE_RATE)
    active_sample_rate = models.FloatField(default=settings.DEFAULT_SAMPLE_RATE)
    active_window_end = models.DateTimeField(null=True, blank=True)

    # Sentry Api
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="apps")
    env = models.CharField(max_length=50, null=True, blank=True)
    command = models.CharField(max_length=50, null=True, blank=True)

    # WSGI
    wsgi_ignore_path = ArrayField(
        models.CharField(max_length=50, blank=True),
        blank=True,
        default=partial(settings_default_value, "DEFAULT_WSGI_IGNORE_PATHS"),
    )
    wsgi_collect_metrics = models.BooleanField(default=False)
    wsgi_metrics = models.JSONField(null=True, blank=True)

    # celery
    celery_ignore_task = ArrayField(
        models.CharField(max_length=50, blank=True),
        blank=True,
        default=partial(settings_default_value, "DEFAULT_CELERY_IGNORE_TASKS"),
    )
    celery_collect_metrics = models.BooleanField(default=False)
    celery_metrics = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"App<{self.reference}>"

    def merge(self, validated_data):
        merger = MERGER[validated_data["type"]]
        merger(self, validated_data["data"])
        self.last_seen = timezone.now()

    def get_metric(self, metric_type: MetricType):
        prefix = metric_type.value.lower()
        return getattr(self, f"{prefix}_collect_metrics"), getattr(self, f"{prefix}_metrics")

    def set_metric(self, metric_type: MetricType, metric_state: bool):
        prefix = metric_type.value.lower()
        setattr(self, f"{prefix}_collect_metrics", metric_state)

    class Meta:
        permissions = [
            ("bump_sample_rate_app", "Can bump sample rate"),
            ("panic_app", "Panic! Set all sample rate to 0"),
            ("enable_disable_metrics_app", "Can Enable/Disable metrics"),
        ]
