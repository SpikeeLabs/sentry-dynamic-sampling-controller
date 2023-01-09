from collections import Counter


def celery_merger(old, new):
    return Counter(old) + Counter(new)
