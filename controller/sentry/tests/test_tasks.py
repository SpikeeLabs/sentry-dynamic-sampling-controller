from collections import OrderedDict
from datetime import timedelta
from unittest.mock import MagicMock, call, patch

import pytest
from dateutil import parser
from django.conf import settings
from django.utils import timezone

from controller.sentry.choices import EventType
from controller.sentry.models import App, Event, Project
from controller.sentry.tasks import (
    close_window,
    monitor_sentry_usage,
    perform_detect,
    populate_app,
    prune_inactive_app,
    prune_old_event,
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

    project = Project(sentry_id="abc")
    project.save()
    app = App(reference="abc", project=project)
    app.save()

    unlink_project = Project(sentry_id="123")
    unlink_project.save()

    prune_inactive_app()
    assert Project.objects.filter(sentry_id=project.sentry_id).exists()
    assert not Project.objects.filter(sentry_id=unlink_project.sentry_id).exists()


@pytest.mark.django_db
def test_prune_old_event():
    project = Project(sentry_id="123")
    project.save()
    event = Event(type=EventType.DISCARD, timestamp=timezone.now(), project=project)
    event.save()
    prune_old_event()
    assert Event.objects.filter(reference=event.reference).exists()

    event = Event(
        type=EventType.DISCARD,
        timestamp=timezone.now() - timedelta(days=settings.EVENT_AUTO_PRUNE_MAX_AGE_DAY + 1),
        project=project,
    )
    event.save()
    prune_old_event()
    assert not Event.objects.filter(reference=event.reference).exists()


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
    project = Project(sentry_id="123")
    project.save()
    pull_sentry_project_slug()
    client_mock.assert_called_once_with()

    project.refresh_from_db()
    assert project.sentry_project_slug == "test"


@pytest.mark.django_db
def test_populate_app():
    app = App(reference="123_env_command")
    app.save()
    populate_app()

    app.refresh_from_db()
    assert app.env == "env"
    assert app.command == "command"
    assert app.project is not None
    assert app.project.sentry_id == "123"


@pytest.mark.django_db
def test_populate_app_wrong_reference():
    app = App(reference="123_env")
    app.save()
    populate_app()

    app.refresh_from_db()
    assert app.env is None
    assert app.command is None
    assert app.project is None


@patch("controller.sentry.tasks.group")
@patch("controller.sentry.tasks.perform_detect")
@pytest.mark.django_db
def test_monitor_sentry_usage(perform_detect_mock: MagicMock, group_mock: MagicMock):
    project1 = Project(sentry_id="123")
    project1.save()

    project2 = Project(sentry_id="456")
    project2.save()

    monitor_sentry_usage()

    group_mock.assert_called()

    # force generator to call perform_detect_mock
    list(group_mock.call_args[0][0])

    perform_detect_mock.s.assert_has_calls([call("123"), call("456")])


@patch("controller.sentry.tasks.PaginatedSentryClient")
@patch("controller.sentry.tasks.SpikesDetector")
@pytest.mark.django_db
def test_perform_detect(spike_detector_mock: MagicMock, client_mock: MagicMock):
    sentry_id = "123"
    project = Project(sentry_id=sentry_id)
    project.save()

    event = Event(project=project, type=EventType.DISCARD, timestamp=parser.parse("2023-02-01T17:00:00Z"))
    event.save()

    result = object()
    client_mock.return_value.get_stats.return_value = result

    detector: MagicMock = spike_detector_mock.from_project.return_value
    dump = {"test": "a"}
    detector.compute_sentry.return_value = (
        OrderedDict(
            [
                ("2023-02-01T15:00:00Z", 0),
                ("2023-02-01T16:00:00Z", 1),
                ("2023-02-01T17:00:00Z", 0),
                ("2023-02-01T18:00:00Z", 1),
                ("2023-02-01T19:00:00Z", 0),
            ]
        ),
        dump,
    )

    perform_detect(sentry_id)

    client_mock.assert_called_once_with()
    client_mock.return_value.get_stats.assert_called_once_with(sentry_id)

    spike_detector_mock.from_project.assert_called_once_with(project)

    detector.compute_sentry.assert_called_once_with(result)

    project.refresh_from_db()
    assert project.events.exclude(reference=event.reference).count() == 2
    assert project.detection_result == dump
