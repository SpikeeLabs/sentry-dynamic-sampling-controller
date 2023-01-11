# -- coding: UTF-8 --
import os

worker_class = "gevent"
workers = int(os.getenv("WORKERS", "4"))
bind = [
    f'{os.environ.get("HTTP_ADDR", "0.0.0.0")}:{os.environ.get("HTTP_PORT", "8000")}'
]
daemon = os.environ.get("DEAMON_RUNNING", False)
timeout = os.environ.get("TIMEOUT", 60)
loglevel = os.environ.get("LOG_LEVEL", "info")
errorlog = os.environ.get("ERROR_LOG", "-")
accesslog = os.environ.get("ACCESS_LOG", "-")
