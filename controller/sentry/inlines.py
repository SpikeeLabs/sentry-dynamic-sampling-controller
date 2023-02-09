from django.contrib import admin
from nonrelated_inlines.admin import NonrelatedTabularInline

from controller.sentry.mixins import PrettyTypeMixin
from controller.sentry.models import Event


class EventInlineMixin(PrettyTypeMixin):
    model = Event
    fields = ("reference", "pretty_type", "timestamp", "project")
    readonly_fields = fields
    can_delete = False
    extra = 0
    show_change_link = True

    ordering = ("-timestamp",)

    def has_add_permission(self, request, obj=None) -> bool:  # pylint: disable=unused-argument
        return False


class ProjectEventInline(EventInlineMixin, admin.TabularInline):
    pass


class AppEventInline(EventInlineMixin, NonrelatedTabularInline):
    def get_form_queryset(self, obj):
        if obj.project is None:
            return Event.objects.none()
        return obj.project.events.all()

    def save_new_instance(self, parent, instance):  # pylint: disable=unused-argument
        raise NotImplementedError
