from collections import Counter


def wsgi_merger(old, new):
    return dict(Counter(old) + Counter(new))
