"""Filters."""

from typing import TYPE_CHECKING

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from controller.sentry.choices import EventType

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.admin import ModelAdmin
    from django.db.models import QuerySet
    from django.http import HttpRequest

    from controller.sentry.models import App


class IsSpammingListFilter(admin.SimpleListFilter):
    """Is Spamming filter."""

    title = _("Spamming Sentry")

    parameter_name = "spamming"

    def lookups(self, request: "HttpRequest", model_admin: "ModelAdmin") -> tuple:
        """Lookup.

        Args:
            request (HttpRequest): The request
            model_admin (ModelAdmin): The admin

        Returns:
            tuple: The lookup field
        """
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request: "HttpRequest", queryset: "QuerySet[App]") -> "QuerySet[App]":
        """Return the filtered queryset.

        Args:
            request (HttpRequest): The request
            queryset (QuerySet[App]): The queryset

        Returns:
            QuerySet[App]: The filtered queryset
        """
        if (value := self.value()) is None:
            return queryset

        event_type = EventType.DISCARD if value == "no" else EventType.FIRING

        return queryset.filter(project__last_event__type=event_type)
