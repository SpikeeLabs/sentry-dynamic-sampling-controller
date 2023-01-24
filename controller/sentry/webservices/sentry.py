from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Generator
from urllib.parse import urljoin

from celery.utils.log import get_task_logger
from django.conf import settings
from requests.api import request
from requests.auth import AuthBase
from requests.models import Response

from controller.sentry.utils import Singleton

LOGGER = get_task_logger(__name__)


class BearerAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class PaginatedSentryClient(metaclass=Singleton):
    def __init__(self) -> None:
        self.host = "https://sentry.io/api/0/"
        self.auth = BearerAuth(settings.SENTRY_TOKEN)

    def __call(self, method: str, url):
        while True:
            response = request(method, url, timeout=20, auth=self.auth)

            # Checks if the response is rate limited
            if response.status_code == 429:
                window_end_timestamp = int(response.headers.get("x-sentry-rate-limit-reset"))
                window_end = datetime.fromtimestamp(window_end_timestamp, tz=timezone.utc)
                wait_period: timedelta = window_end - datetime.now(timezone.utc)
                retry = max(wait_period.total_seconds(), 1)
                LOGGER.error("Got HTTP 429 on %s waiting %s", url, retry, extra=dict(response.headers))
                sleep(retry)
            else:
                response.raise_for_status()
                return response

    def __get_next(self, response: Response):
        _next = response.links.get("next")
        if _next is None or _next["results"] == "false":
            return None
        return _next["url"]

    def __paginated(self, url):
        while True:
            response = self.__call("GET", url)
            yield response.json()

            url = self.__get_next(response)

            if url is None:
                break

    def list_projects(self) -> Generator[list[dict], None, None]:
        url = urljoin(self.host, "projects/")
        return self.__paginated(url)
