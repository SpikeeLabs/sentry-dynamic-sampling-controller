from datetime import timedelta
from itertools import chain

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import F
from django.utils import timezone

from controller.sentry.models import App
from controller.sentry.webservices.sentry import PaginatedSentryClient

LOGGER = get_task_logger(__name__)


@shared_task()
def prune_inactive_app() -> None:
    last_seen = timezone.now() - timedelta(days=settings.APP_AUTO_PRUNE_MAX_AGE_DAY)
    apps = App.objects.filter(last_seen__lt=last_seen)
    if apps_count := apps.count():
        LOGGER.info("Pruning %s apps", apps_count)
        apps.delete()


@shared_task()
def close_window() -> None:
    apps = App.objects.filter(active_window_end__lt=timezone.now())
    apps.update(active_sample_rate=F("default_sample_rate"), active_window_end=None)


@shared_task()
def pull_sentry_project_slug() -> None:
    client = PaginatedSentryClient()
    apps = App.objects.filter(sentry_project_slug__isnull=True)

    apps_by_id = {app.get_sentry_id(): app for app in apps}

    modified_apps = []
    for project in chain.from_iterable(client.list_projects()):
        _id = project["id"]
        if _id in apps_by_id:
            app = apps_by_id[_id]
            app.sentry_project_slug = project["slug"]
            modified_apps.append(app)

    App.objects.bulk_update(modified_apps, ["sentry_project_slug"])
