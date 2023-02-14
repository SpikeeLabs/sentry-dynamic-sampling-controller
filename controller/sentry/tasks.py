"""Tasks."""
from datetime import timedelta
from itertools import chain
from typing import Optional

from celery import group, shared_task
from celery.utils.log import get_task_logger
from dateutil import parser
from django.conf import settings
from django.db.models import Count, F
from django.utils import timezone

from controller.sentry.choices import EventType
from controller.sentry.detector import SpikesDetector
from controller.sentry.exceptions import SentryNoOutcomeException
from controller.sentry.models import App, Event, Project
from controller.sentry.webservices.sentry import PaginatedSentryClient

LOGGER = get_task_logger(__name__)


@shared_task()
def populate_app() -> None:
    """This task is responsible for populating apps.

    For each new app, link the associated project to the app.

    This task should be run regularly.
    """
    apps = App.objects.filter(project__isnull=True)
    for app in apps:
        res = app.reference.split("_")
        if len(res) == 3:
            sentry_id, env, command = res
            project, _ = Project.objects.get_or_create(sentry_id=sentry_id)
            app = App.objects.filter(reference=app.reference).update(command=command, env=env, project=project)


@shared_task()
def prune_inactive_app() -> None:
    """This task is responsible for pruning apps and projects.

    For each app not seen in `settings.APP_AUTO_PRUNE_MAX_AGE_DAY` days, remove the app.

    For each project with no apps, remove the project.

    This task should be run regularly.
    """
    last_seen = timezone.now() - timedelta(days=settings.APP_AUTO_PRUNE_MAX_AGE_DAY)
    apps = App.objects.filter(last_seen__lt=last_seen)
    if apps_count := apps.count():
        LOGGER.info("Pruning %s apps", apps_count)
        apps.delete()
    projects = Project.objects.annotate(apps_count=Count("apps")).filter(apps_count=0)
    if projects_count := projects.count():
        LOGGER.info("Pruning %s projects", projects_count)
        projects.delete()


@shared_task()
def prune_old_event() -> None:
    """This task is responsible for pruning old event.

    Remove all event older than `settings.EVENT_AUTO_PRUNE_MAX_AGE_DAY` days.

    This task should be run regularly.
    """
    period_end = timezone.now() - timedelta(days=settings.EVENT_AUTO_PRUNE_MAX_AGE_DAY)
    events = Event.objects.filter(timestamp__lt=period_end)
    if events_count := events.count():
        LOGGER.info("Pruning %s apps", events_count)
        events.delete()


@shared_task()
def close_window() -> None:
    """This task is responsible for closing sample rate window.

    For all apps with an `active_window_end` in the pass.
    Close the windows by setting

        * `active_sample_rate` to `default_sample_rate`
        * `active_window_end` to null

    This task should be run regularly.
    """
    apps = App.objects.filter(active_window_end__lt=timezone.now())
    apps.update(active_sample_rate=F("default_sample_rate"), active_window_end=None)


@shared_task()
def pull_sentry_project_slug() -> None:
    """This task is responsible for getting the project slug from Sentry API.

    For all projects without a `sentry_project_slug`.
    Find their project slug and update the project

    This task should be run regularly.
    """
    client = PaginatedSentryClient()
    projects = Project.objects.filter(sentry_project_slug__isnull=True)

    projects_by_id = {project.sentry_id: project for project in projects}

    modified_projects = []
    for project in chain.from_iterable(client.list_projects()):
        _id = project["id"]
        if _id not in projects_by_id:
            continue
        projects_by_id[_id].sentry_project_slug = project["slug"]
        modified_projects.append(projects_by_id[_id])

    Project.objects.bulk_update(modified_projects, ["sentry_project_slug"])


@shared_task()
def monitor_sentry_usage() -> None:
    """This task is responsible for starting all the perform_detect tasks."""
    projects = Project.objects.all()
    group(perform_detect.s(p.sentry_id) for p in projects).delay()


@shared_task()
def perform_detect(sentry_id) -> None:
    """This task is responsible for the spike detection.

    Get stats for this project and run the spike detection algorithm

    Args:
        sentry_id (str): The sentry id of the project
    """
    client = PaginatedSentryClient()
    project = Project.objects.get(sentry_id=sentry_id)

    stats = client.get_stats(project.sentry_id)
    detector = SpikesDetector.from_project(project)
    try:
        res, dump = detector.compute_sentry(stats)
    except SentryNoOutcomeException:
        return

    project.detection_result = dump
    project.save()

    previous_signal = 0
    events = []
    last_event: Optional[Event] = project.events.last()

    for date, signal in res.items():
        if previous_signal == signal:
            continue

        date = parser.parse(date)

        if last_event and date <= last_event.timestamp:
            previous_signal = signal
            continue

        event_type = EventType.FIRING if previous_signal == 0 else EventType.DISCARD
        events.append(Event(type=event_type, project=project, timestamp=date))
        previous_signal = signal

    Event.objects.bulk_create(events)
