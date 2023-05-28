"""Celery Metrics."""
from collections import Counter
from typing import TYPE_CHECKING, Union

from controller.sentry.utils import depth

if TYPE_CHECKING:  # pragma: no cover
    from controller.sentry.models import App


def celery_merger(app: "App", new: Union[dict[str, int], dict[str, dict[str, int]]]) -> None:
    """celery_merger function is used to merge :attr:`Celery <controller.sentry.choices.MetricType.CELERY>` metrics.

    Args:
        app (App): The app associated to the metric
        new (dict[str, int]): The new metric dict
    """
    # Code for Migration
    if depth(app.celery_metrics) == 1:
        app.celery_metrics = {"task": app.celery_metrics}

    if depth(new) == 1:
        new = {"task": new}
    # End of migration code

    if app.celery_metrics is None:
        app.celery_metrics = {}

    tmp = {}
    for key in set(list(app.celery_metrics.keys()) + list(new.keys())):
        old_value = app.celery_metrics.get(key)
        new_value = new.get(key)
        tmp[key] = dict(Counter(old_value) + Counter(new_value))

    app.celery_metrics = tmp
