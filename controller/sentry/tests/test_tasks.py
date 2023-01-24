from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.utils import timezone

from controller.sentry.models import App
from controller.sentry.tasks import (
    close_window,
    prune_inactive_app,
    pull_sentry_project_slug,
)


@pytest.mark.django_db
def test_prune_inactive_app():
    app = App(reference="abc")
    app.save()
    prune_inactive_app()
    assert App.objects.filter(reference=app.reference).exists()

    app.last_seen = timezone.now() - timedelta(days=settings.APP_AUTO_PRUNE_MAX_AGE_DAY + 1)
    app.save()
    prune_inactive_app()
    assert not App.objects.filter(reference=app.reference).exists()


@pytest.mark.django_db
def test_close_window():
    tomorrow = timezone.now() + timedelta(days=1)
    app = App(reference="abc1", active_window_end=tomorrow, active_sample_rate=1)
    app.save()
    close_window()
    app.refresh_from_db()
    assert app.active_sample_rate == 1
    assert app.active_window_end == tomorrow

    app = App(reference="abc2", active_window_end=timezone.now(), active_sample_rate=1)
    app.save()
    close_window()
    app.refresh_from_db()
    assert app.active_sample_rate == app.default_sample_rate
    assert app.active_window_end is None


@patch("controller.sentry.tasks.PaginatedSentryClient")
@pytest.mark.django_db
def test_pull_sentry_project_slug(client_mock: MagicMock):
    client_mock.return_value.list_projects.return_value = [
        [],
        [{"id": "123", "slug": "test"}],
        [{"id": "1235", "slug": "test2"}],
    ]
    app = App(reference="123_prod_wsgi")
    app.save()
    pull_sentry_project_slug()
    client_mock.assert_called_once_with()

    app.refresh_from_db()
    assert app.sentry_project_slug == "test"
