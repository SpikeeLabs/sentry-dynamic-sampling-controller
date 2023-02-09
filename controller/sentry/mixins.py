from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from controller.sentry.choices import EventType


class PrettyTypeMixin:
    def pretty_type(self, obj):
        color = "red" if obj.type == EventType.FIRING else "green"
        text = obj.type.capitalize()
        return format_html('<b style="color:{};">{}</b>', color, text)


class ProjectLinkMixin:
    @admin.display(ordering="project__sentry_project_slug", description="project")
    def get_project(self, obj):
        if obj.project is None:
            return None
        url = reverse("admin:%s_%s_change" % (self.model._meta.app_label, "project"), args=(obj.project.pk,))
        return format_html('<a href="%s">%s</a>' % (url, str(obj.project)))


class ChartMixin:
    change_form_template = "admin/chart_change_form.html"

    def change_view(self, request, object_id, form_url="", extra_context=None):

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
