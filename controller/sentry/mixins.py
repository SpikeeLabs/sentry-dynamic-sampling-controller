"""Mixins."""

from typing import TYPE_CHECKING, Optional, Union

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from controller.sentry.choices import EventType

if TYPE_CHECKING:  # pragma: no cover
    from django.http import HttpRequest, HttpResponse

    from controller.sentry.models import App, Event


class PrettyTypeMixin:
    """Mixin to add a pretty event type."""

    def pretty_type(self, obj: "Event") -> str:
        """Pretty event type.

        Args:
            obj (Event): The event

        Returns:
            str: Pretty type
        """
        color = "red" if obj.type == EventType.FIRING else "green"
        text = obj.type.capitalize()
        return format_html('<b style="color:{};">{}</b>', color, text)


class ProjectLinkMixin:
    """Mixin to get a project link."""

    @admin.display(ordering="project__sentry_project_slug", description="project")
    def get_project(self, obj: "Union[Event, App]") -> str:
        """Get project link.

        Args:
            obj (Union[Event, App]): Event or App

        Returns:
            str: Petty formatted html link
        """
        if obj.project is None:
            return None
        url = reverse("admin:%s_%s_change" % (self.model._meta.app_label, "project"), args=(obj.project.pk,))
        return format_html('<a href="%s">%s</a>' % (url, str(obj.project)))


class ChartMixin:
    """Mixin to get a chart on admin."""

    change_form_template = "admin/chart_change_form.html"

    def change_view(
        self, request: "HttpRequest", object_id: str, form_url: str = "", extra_context: Optional[dict] = None
    ) -> "HttpResponse":
        """Method used to inject Chart data.

        Args:
            request (HttpRequest): Http request
            object_id (str): object id
            form_url (str): form_url (Default to Blank string)
            extra_context (Optional[dict]): extra context  (Default to None)
        """
        if extra_context is None:
            extra_context = {}

        if result := self.get_chart_data(object_id):
            dataset, options = result
            extra_context["adminchart_chartjs_config"] = {
                "type": "line",
                "data": dataset,
                "options": options,
            }

        return super().change_view(request, object_id, form_url, extra_context)
