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
