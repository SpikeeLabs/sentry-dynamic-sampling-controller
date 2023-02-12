"""loadpermissions command."""
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """loadpermissions command."""

    help = "Set default permissions."  # noqa: A003

    def handle(self, *args, **options):
        """Handle the loadpermissions command.

        This command set the default permissions of groups
            * Owner (all access)
            * Admin (all access on sentry app)
            * Developer (view sentry object and use developer actions)
            * Viewer (view sentry object)

        """
        owner, _ = Group.objects.get_or_create(name="Owner")
        admin, _ = Group.objects.get_or_create(name="Admin")
        developer, _ = Group.objects.get_or_create(name=settings.DEVELOPER_GROUP)
        viewer, _ = Group.objects.get_or_create(name="Viewer")

        owner.permissions.set(Permission.objects.all())
        admin.permissions.set(Permission.objects.filter(content_type__app_label="sentry"))

        view_permission = Permission.objects.filter(codename__contains="view_", content_type__app_label="sentry")

        developer.permissions.set(
            chain(view_permission.all(), Permission.objects.filter(codename__in=settings.DEVELOPER_ACTIONS))
        )

        viewer.permissions.set(view_permission.all())
