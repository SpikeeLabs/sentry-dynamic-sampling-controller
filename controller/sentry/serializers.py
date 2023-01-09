from rest_framework import serializers

from controller.sentry.models import App, Metric


class AppSerializer(serializers.ModelSerializer):
    """App"""

    class Meta:
        model = App
        fields = [
            "reference",
            "active_sample_rate",
            "active_window_end",
            "wsgi_ignore_path",
            "celery_ignore_task",
        ]


class MetricSerializer(serializers.ModelSerializer):
    """Metric"""

    class Meta:
        model = Metric
        fields = ["type", "app", "data", "last_updated"]
