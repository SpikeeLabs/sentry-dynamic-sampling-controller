from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import decorators, viewsets
from rest_framework.response import Response

from controller.sentry.models import App, Metric
from controller.sentry.serializers import AppSerializer, MetricSerializer


class AppViewSet(viewsets.ModelViewSet):
    """App"""

    model = App
    serializer_class = AppSerializer
    queryset = App.objects.all()

    @method_decorator(cache_page(settings.APP_CACHE_TIMEOUT))
    def retrieve(self, request, *args, **kwargs):
        app, _ = App.objects.get_or_create(**kwargs)
        now = timezone.now()
        app.last_seen = now
        if app.active_window_end and app.active_window_end < now:
            app.active_sample_rate = app.default_sample_rate
        app.save()
        serializer = self.get_serializer(app)
        return Response(serializer.data)

    @decorators.action(
        detail=True, methods=["post"], url_path=r"metrics/(?P<metric_name>[^/.]+)"
    )
    def metrics(
        self, request, pk=None, metric_name=None
    ):  # pylint: disable=W0613,C0103
        app, _ = App.objects.get_or_create(reference=pk)
        metric, _ = Metric.objects.get_or_create(app=app, type=metric_name, defaults={})

        serializer = MetricSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        metric.merge(serializer.validated_data["data"])
        metric.save()
        return Response(MetricSerializer(instance=metric).data)


class MetricViewSet(viewsets.ModelViewSet):
    """Metric"""

    model = Metric
    serializer_class = MetricSerializer
    queryset = Metric.objects.all()
