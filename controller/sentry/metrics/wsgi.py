from collections import Counter


def wsgi_merger(app, new):
    app.wsgi_metrics = dict(Counter(app.wsgi_metrics) + Counter(new))
