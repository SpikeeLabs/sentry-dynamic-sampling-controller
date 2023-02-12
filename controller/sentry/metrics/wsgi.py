"""Wsgi Metrics."""
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from controller.sentry.models import App


def wsgi_merger(app: "App", new: dict[str, int]) -> None:
    """wsgi_merger function is used to merge :attr:`WSGI <controller.sentry.choices.MetricType.WSGI>` metrics.

    Args:
        app (App): The app associated to the metric
        new (dict[str, int]): The new metric dict
    """
    app.wsgi_metrics = dict(Counter(app.wsgi_metrics) + Counter(new))
