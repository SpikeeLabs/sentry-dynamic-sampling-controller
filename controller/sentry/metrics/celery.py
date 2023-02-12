"""Celery Metrics."""
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from controller.sentry.models import App


def celery_merger(app: "App", new: dict[str, int]) -> None:
    """celery_merger function is used to merge :attr:`Celery <controller.sentry.choices.MetricType.CELERY>` metrics.

    Args:
        app (App): The app associated to the metric
        new (dict[str, int]): The new metric dict
    """
    app.celery_metrics = dict(Counter(app.celery_metrics) + Counter(new))
