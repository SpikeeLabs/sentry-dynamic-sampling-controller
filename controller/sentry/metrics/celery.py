from collections import Counter


def celery_merger(old, new):
    return dict(Counter(old) + Counter(new))
