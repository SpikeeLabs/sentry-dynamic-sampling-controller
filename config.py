# -- coding: UTF-8 --
import os
import socket

worker_class = "gevent"
workers = int(os.getenv("WORKERS", "4"))
bind = [f'{os.environ.get("HTTP_ADDR", "0.0.0.0")}:{os.environ.get("HTTP_PORT", "8000")}']
daemon = os.environ.get("DEAMON_RUNNING", False)
timeout = os.environ.get("TIMEOUT", 60)
loglevel = os.environ.get("LOG_LEVEL", "info")
errorlog = os.environ.get("ERROR_LOG", "-")
accesslog = os.environ.get("ACCESS_LOG", "-")


_statsd_host = os.getenv("STATSD_HOST")
_statsd_port = os.getenv("STATSD_PORT")
if _statsd_host and _statsd_port:
    statsd_host = f"{_statsd_host}:{_statsd_port}"
    statsd_prefix = socket.gethostname()
