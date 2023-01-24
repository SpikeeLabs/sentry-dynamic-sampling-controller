from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import decorators, mixins, viewsets
from rest_framework.response import Response

from controller.sentry.models import App
from controller.sentry.serializers import AppSerializer, MetricSerializer


class AppViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """App"""

    model = App
    serializer_class = AppSerializer
    queryset = App.objects.all()

    @method_decorator(cache_page(settings.APP_CACHE_TIMEOUT))
    def retrieve(self, request, *args, **kwargs):
        app, _ = App.objects.get_or_create(**kwargs)
        panic = cache.get(settings.PANIC_KEY)
        now = timezone.now()
        app.last_seen = now
        app.save()
        if panic:
            app.active_sample_rate = 0.0
        serializer = self.get_serializer(app)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=["post"], url_path=r"metrics/(?P<metric_name>[^/.]+)")
    def metrics(self, request, pk=None, metric_name=None):  # pylint: disable=W0613,C0103
        app, _ = App.objects.get_or_create(reference=pk)

        serializer = MetricSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app.merge(serializer.validated_data)
        app.save()
        return Response({})
