from django.contrib import admin

from controller.sentry.models import Metric


class MetricsInline(admin.TabularInline):
    model = Metric
    fields = ("type", "app", "last_updated", "data")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    classes = ["collapse"]

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
