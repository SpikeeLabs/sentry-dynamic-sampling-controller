from collections import Counter


def celery_merger(app, new):
    app.celery_metrics = dict(Counter(app.celery_metrics) + Counter(new))
