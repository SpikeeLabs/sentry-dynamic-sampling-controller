"""Wsgi Metrics."""
from collections import Counter
from typing import TYPE_CHECKING, Union

from controller.sentry.utils import depth

if TYPE_CHECKING:  # pragma: no cover
    from controller.sentry.models import App


def wsgi_merger(app: "App", new: Union[dict[str, int], dict[str, dict[str, int]]]) -> None:
    """wsgi_merger function is used to merge :attr:`WSGI <controller.sentry.choices.MetricType.WSGI>` metrics.

    Args:
        app (App): The app associated to the metric
        new (dict[str, int]): The new metric dict
    """
    # Code for Migration
    if depth(app.wsgi_metrics) == 1:
        app.wsgi_metrics = {"path": app.wsgi_metrics}

    if depth(new) == 1:
        new = {"path": new}
    # End of migration code

    if app.wsgi_metrics is None:
        app.wsgi_metrics = {}

    tmp = {}
    for key in set(list(app.wsgi_metrics.keys()) + list(new.keys())):
        old_value = app.wsgi_metrics.get(key)
        new_value = new.get(key)
        tmp[key] = dict(Counter(old_value) + Counter(new_value))

    app.wsgi_metrics = tmp
