from admin_action_tools import (
    ActionFormMixin,
    AdminConfirmMixin,
    add_form_to_action,
    confirm_action,
)
from django.contrib import admin
from django.db import models
from django.utils import timezone
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions, takes_instance_or_queryset

from controller.sentry.forms import BumpForm
from controller.sentry.inlines import MetricsInline
from controller.sentry.models import App, Metric


@admin.register(App)
class AppAdmin(
    AdminConfirmMixin,
    ActionFormMixin,
    DjangoObjectActions,
    DynamicArrayMixin,
    admin.ModelAdmin,
):
    read_only_fields = ["last_seen"]

    list_display = [
        "reference",
        "last_seen",
        "default_sample_rate",
        "active_sample_rate",
        "active_window_end",
    ]

    search_fields = [
        "reference",
    ]
    ordering = search_fields

    fieldsets = [
        [
            None,
            {
                "fields": (
                    ("reference", "last_seen"),
                    "default_sample_rate",
                    ("active_sample_rate", "active_window_end"),
                )
            },
        ],
        [
            "WSGI",
            {"fields": ("wsgi_ignore_path",)},
        ],
        [
            "Celery",
            {"fields": ("celery_ignore_task",)},
        ],
    ]

    changelist_actions = ["bump"]
    change_actions = ["bump"]

    inlines = [MetricsInline]

    @takes_instance_or_queryset
    @add_form_to_action(BumpForm)
    @confirm_action()
    @admin.action(description="Bump Sample Rate")
    def bump(self, request, queryset, form: BumpForm = None):
        new_date = timezone.now() + form.cleaned_data["duration"]
        queryset.update(
            active_sample_rate=form.cleaned_data["new_sample_rate"],
            active_window_end=new_date,
        )


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }

    list_display = [
        "type",
        "last_updated",
        "app",
    ]

    search_fields = ["type", "last_updated", "app__reference"]
    ordering = search_fields

    fieldsets = [
        [
            None,
            {
                "fields": (
                    ("type", "last_updated", "app"),
                    "data",
                )
            },
        ]
    ]
