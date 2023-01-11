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
from controller.sentry.models import App
from controller.sentry.utils import invalidate_cache


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

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }

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
            {
                "classes": ("collapse", "open"),
                "fields": ("wsgi_ignore_path", "wsgi_collect_metrics", "wsgi_metrics"),
            },
        ],
        [
            "Celery",
            {
                "classes": ("collapse", "open"),
                "fields": (
                    "celery_ignore_task",
                    "celery_collect_metrics",
                    "celery_metrics",
                ),
            },
        ],
    ]

    changelist_actions = ["bump"]
    change_actions = ["bump"]

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

    def save_model(self, request, obj, form, change) -> None:
        invalidate_cache(f"/sentry/apps/{obj.reference}/")
        return super().save_model(request, obj, form, change)
