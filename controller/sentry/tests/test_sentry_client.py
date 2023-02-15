from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest
from django.conf import settings
from requests.exceptions import HTTPError

from controller.sentry.webservices.sentry import BearerAuth, PaginatedSentryClient


class Response:
    def __init__(self, status_code, data, links=None, headers=None) -> None:
        self.status_code = status_code
        self.data = data
        self.links = links if links else {}
        self.headers = headers if headers else {}

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code > 399:
            raise HTTPError


def test_auth():
    auth = BearerAuth("my_token")
    request_mock = MagicMock()
    auth(request_mock)

    request_mock.headers.__setitem__.assert_called_once_with("authorization", "Bearer my_token")


@patch("controller.sentry.webservices.sentry.request")
def test_client(mock_request: MagicMock):
    client = PaginatedSentryClient()

    res = client.list_projects()
    mock_request.assert_not_called()
    return_value = [
        Response(200, [object(), object()], links={"next": {"results": True, "url": "http://next.sentry"}}),
        Response(200, [object(), object()]),
    ]

    mock_request.side_effect = return_value

    for chunk, expected in zip(res, return_value):
        assert chunk == expected.data

    call_1 = call("GET", "https://sentry.io/api/0/projects/", timeout=20, auth=client.auth, params=None)
    call_2 = call("GET", "http://next.sentry", timeout=20, auth=client.auth, params=None)
    mock_request.assert_has_calls((call_1, call_2))


@patch("controller.sentry.webservices.sentry.request")
def test_client_rate_limited(mock_request: MagicMock):
    client = PaginatedSentryClient()

    res = client.list_projects()
    mock_request.assert_not_called()
    reset = datetime.now() + timedelta(seconds=5)
    return_value = [
        Response(429, [object(), object()], headers={"x-sentry-rate-limit-reset": reset.timestamp()}),
        Response(500, [object(), object()]),
    ]

    mock_request.side_effect = return_value

    with pytest.raises(HTTPError):
        next(res)

    call_1 = call("GET", "https://sentry.io/api/0/projects/", timeout=20, auth=client.auth, params=None)
    call_2 = call("GET", "https://sentry.io/api/0/projects/", timeout=20, auth=client.auth, params=None)
    mock_request.assert_has_calls((call_1, call_2))


@patch("controller.sentry.webservices.sentry.request")
def test_client_rate_limited_rest_in_past(mock_request: MagicMock):
    client = PaginatedSentryClient()

    res = client.list_projects()
    mock_request.assert_not_called()

    reset = datetime.now() - timedelta(seconds=5)
    return_value = [
        Response(429, [object(), object()], headers={"x-sentry-rate-limit-reset": reset.timestamp()}),
        Response(500, [object(), object()]),
    ]

    mock_request.side_effect = return_value

    with pytest.raises(HTTPError):
        next(res)

    call_1 = call("GET", "https://sentry.io/api/0/projects/", timeout=20, auth=client.auth, params=None)
    call_2 = call("GET", "https://sentry.io/api/0/projects/", timeout=20, auth=client.auth, params=None)
    mock_request.assert_has_calls((call_1, call_2))


@patch("controller.sentry.webservices.sentry.request")
def test_client_get_stats(mock_request: MagicMock):
    client = PaginatedSentryClient()

    return_value = [
        Response(200, object()),
    ]
    sentry_id = "1234"
    mock_request.side_effect = return_value
    res = client.get_stats(sentry_id)

    assert res == return_value[0].data

    mock_request.assert_called_once_with(
        "GET",
        f"https://sentry.io/api/0/organizations/{settings.SENTRY_ORGANIZATION_SLUG}/stats_v2/",
        timeout=20,
        auth=client.auth,
        params={
            "field": "sum(quantity)",
            "groupBy": ["category", "outcome"],
            "interval": "1h",
            "project": sentry_id,
            "statsPeriod": settings.SENTRY_STATS_PERIOD,
            "category": "transaction",
        },
    )
