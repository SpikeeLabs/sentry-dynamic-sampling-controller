from collections import Counter


def wsgi_merger(old, new):
    return Counter(old) + Counter(new)
