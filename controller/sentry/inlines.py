"""Inline."""
from typing import TYPE_CHECKING, Optional

from django.contrib import admin
from nonrelated_inlines.admin import NonrelatedTabularInline

from controller.sentry.mixins import PrettyTypeMixin
from controller.sentry.models import Event

if TYPE_CHECKING:  # pragma: no cover
    from django.db.models import QuerySet

    from controller.sentry.models import App


class EventInlineMixin(PrettyTypeMixin):
    """EventInlineMixin."""

    model = Event
    fields: Optional[list[str]] = ["reference", "pretty_type", "timestamp", "project"]
    readonly_fields: Optional[list[str]] = fields
    can_delete = False
    extra = 0
    show_change_link = True

    ordering: Optional[list[str]] = ["-timestamp"]

    def has_add_permission(self, request, obj=None) -> bool:  # pylint: disable=unused-argument
        """Don't allow adding."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # pylint: disable=unused-argument
        """Don't allow modifying."""
        return False


class ProjectEventInline(EventInlineMixin, admin.TabularInline):
    """ProjectEventInline derived from EventInlineMixin and admin.TabularInline."""


class AppEventInline(EventInlineMixin, NonrelatedTabularInline):
    """ProjectEventInline derived from EventInlineMixin and NonrelatedTabularInline."""

    def get_form_queryset(self, obj: "App") -> "QuerySet[Event]":
        """Get all events.

        Args:
            obj (App): The app

        Returns:
            QuerySet[Event]: all the events

        """
        if obj.project is None:
            return Event.objects.none()
        return obj.project.events.all()

    def save_new_instance(self, parent, instance):  # pylint: disable=unused-argument
        """No save allowed."""
        raise NotImplementedError
