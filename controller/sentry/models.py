from django.conf import settings
from django.db import models
from django.utils import timezone
from django_better_admin_arrayfield.models.fields import ArrayField

from controller.sentry.choices import MetricType
from controller.sentry.metrics import celery_merger, wsgi_merger


def get_default_wsgi_ignore_path():
    return settings.DEFAULT_WSGI_IGNORE_PATHS


def get_default_celery_ignore_task():
    return settings.DEFAULT_CELERY_IGNORE_TASKS


MERGER = {MetricType.WSGI: wsgi_merger, MetricType.CELERY: celery_merger}


class App(models.Model):
    """App"""

    reference = models.CharField(primary_key=True, max_length=256)

    last_seen = models.DateTimeField(null=True, blank=True)
    default_sample_rate = models.FloatField(default=settings.DEFAULT_SAMPLE_RATE)
    active_sample_rate = models.FloatField(default=settings.DEFAULT_SAMPLE_RATE)
    active_window_end = models.DateTimeField(null=True, blank=True)

    # Sentry Api
    sentry_project_slug = models.CharField(max_length=50, null=True, blank=True)

    # WSGI
    wsgi_ignore_path = ArrayField(
        models.CharField(max_length=50, blank=True),
        blank=True,
        default=get_default_wsgi_ignore_path,
    )
    wsgi_collect_metrics = models.BooleanField(default=False)
    wsgi_metrics = models.JSONField(null=True, blank=True)

    # celery
    celery_ignore_task = ArrayField(
        models.CharField(max_length=50, blank=True),
        blank=True,
        default=get_default_celery_ignore_task,
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

    def get_sentry_id(self):
        res = self.reference.split("_")
        if len(res) != 3:
            return None
        return res[0]

    class Meta:
        permissions = [
            ("bump_sample_rate_app", "Can bump sample rate"),
            ("panic_app", "Panic! Set all sample rate to 0"),
        ]
