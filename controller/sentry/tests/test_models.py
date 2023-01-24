from controller.sentry.choices import MetricType
from controller.sentry.models import App


def test_app_model_str():
    app = App(reference="abc")
    assert str(app) == "App<abc>"


def test_app_model_merge():
    app = App(reference="abc")
    app.celery_metrics = {"test1": 5, "test": 5}
    app.merge({"type": MetricType.CELERY, "data": {"test": 1}})
    collect, metrics = app.get_metric(MetricType.CELERY)
    assert not collect
    assert metrics == {"test1": 5, "test": 6}


def test_app_model_get_sentry_id():
    app = App(reference="abc")
    assert app.get_sentry_id() is None
    app = App(reference="123_prod_uwsgi")
    assert app.get_sentry_id() == "123"
