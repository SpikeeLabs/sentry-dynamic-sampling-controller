from rest_framework import serializers

from controller.sentry.choices import MetricType
from controller.sentry.models import App


class AppSerializer(serializers.ModelSerializer):
    """App"""

    class Meta:
        model = App
        fields = [
            "reference",
            "active_sample_rate",
            "active_window_end",
            "wsgi_ignore_path",
            "wsgi_collect_metrics",
            "celery_ignore_task",
            "celery_collect_metrics",
        ]


# pylint: disable=abstract-method
class MetricSerializer(serializers.Serializer):

    type = serializers.ChoiceField(choices=MetricType.choices)
    data = serializers.JSONField()
