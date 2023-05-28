from collections import Counter
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.urls import reverse

from controller.sentry.choices import MetricType
from controller.sentry.models import App


@pytest.mark.django_db
def test_app_view_retrieve(client):
    reference = "test"
    url = reverse("sentry:apps-detail", kwargs={"pk": reference})
    response = client.get(url)
    assert response.status_code == 200
    assert response.data["active_window_end"] is None
    assert response.data["active_sample_rate"] == settings.DEFAULT_SAMPLE_RATE
    assert not response.data["wsgi_collect_metrics"]
    assert not response.data["celery_collect_metrics"]


@patch("controller.sentry.views.cache")
@pytest.mark.django_db
def test_app_view_retrieve_panic(cache: Mock, client):
    reference = "test"
    cache.get.return_value = True
    url = reverse("sentry:apps-detail", kwargs={"pk": reference})
    response = client.get(url)
    assert response.status_code == 200
    assert response.data["active_window_end"] is None
    assert response.data["active_sample_rate"] == 0
    cache.get.assert_called_once_with(settings.PANIC_KEY)


@pytest.mark.django_db
@pytest.mark.parametrize("metric,default_name", [(MetricType.WSGI, "path"), (MetricType.CELERY, "task")])
def test_app_view_metrics(client, metric: MetricType, default_name: str):
    reference = "test"
    data = {"type": metric.value, "data": {"test": 1, "test1": 5}}
    url = reverse("sentry:apps-metrics", kwargs={"pk": reference, "metric_name": metric.value})

    response = client.post(url, data, content_type="application/json")
    assert response.status_code == 200, response.data
    app = App.objects.get(reference=reference)
    _, metric_data = app.get_metric(metric)
    assert metric_data == {default_name: data["data"]}


@pytest.mark.django_db
@pytest.mark.parametrize("metric,default_name", [(MetricType.WSGI, "path"), (MetricType.CELERY, "task")])
def test_app_view_metrics_new(client, metric: MetricType, default_name: str):
    reference = "test"
    data = {"type": metric.value, "data": {default_name: {"test": 1, "test1": 5}}}
    url = reverse("sentry:apps-metrics", kwargs={"pk": reference, "metric_name": metric.value})

    response = client.post(url, data, content_type="application/json")
    assert response.status_code == 200, response.data
    app = App.objects.get(reference=reference)
    _, metric_data = app.get_metric(metric)
    assert metric_data == data["data"]


@pytest.mark.django_db
@pytest.mark.parametrize("metric,default_name", [(MetricType.WSGI, "path"), (MetricType.CELERY, "task")])
def test_app_view_metrics_with_old_value(client, metric: MetricType, default_name: str):
    reference = "test"
    metrics = {"test1": 5, "test": 5}
    app = App(reference=reference)
    app.celery_metrics = metrics
    app.wsgi_metrics = metrics
    app.save()
    data = {"type": metric.value, "data": {default_name: metrics}}
    url = reverse("sentry:apps-metrics", kwargs={"pk": reference, "metric_name": metric.value})

    response = client.post(url, data, content_type="application/json")
    assert response.status_code == 200, response.data
    app = App.objects.get(reference=reference)
    _, metric_data = app.get_metric(metric)
    assert metric_data == {default_name: Counter(metrics) + Counter(metrics)}


@pytest.mark.django_db
def test_app_view_list(client):
    response = client.get("/sentry/apps/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_app_view_post(client):
    response = client.post("/sentry/apps/test/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_app_view_patch(client):
    response = client.patch("/sentry/apps/test/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_app_view_put(client):
    response = client.put("/sentry/apps/test/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_app_view_delete(client):
    response = client.delete("/sentry/apps/test/")
    assert response.status_code == 405
