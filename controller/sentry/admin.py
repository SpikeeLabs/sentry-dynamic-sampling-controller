from admin_action_tools import (
    ActionFormMixin,
    AdminConfirmMixin,
    add_form_to_action,
    confirm_action,
)
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_permission_codename
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_json_widget.widgets import JSONEditorWidget
from django_object_actions import DjangoObjectActions, takes_instance_or_queryset

from controller.sentry.choices import EventType, MetricType
from controller.sentry.forms import BumpForm, MetricForm
from controller.sentry.inlines import AppEventInline, ProjectEventInline
from controller.sentry.mixins import PrettyTypeMixin, ProjectLinkMixin
from controller.sentry.models import App, Event, Project
from controller.sentry.utils import invalidate_cache


@admin.register(Project)
class ProjectAdmin(
    AdminConfirmMixin,
    ActionFormMixin,
    DjangoObjectActions,
    DynamicArrayMixin,
    admin.ModelAdmin,
):

    list_display = [
        "sentry_id",
        "sentry_project_slug",
    ]

    search_fields = ["sentry_id", "sentry_project_slug"]
    ordering = search_fields

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }

    fieldsets = [
        [
            None,
            {"fields": ("sentry_id", "sentry_project_slug", "detection_param")},
        ]
    ]

    inlines = [ProjectEventInline]


@admin.register(Event)
class EventAdmin(
    ProjectLinkMixin,
    AdminConfirmMixin,
    ActionFormMixin,
    DjangoObjectActions,
    DynamicArrayMixin,
    PrettyTypeMixin,
    admin.ModelAdmin,
):

    list_display = ["reference", "pretty_type", "timestamp", "get_project"]

    search_fields = ["reference", "type", "project__sentry_project_slug"]
    ordering = search_fields

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }

    fieldsets = [
        [
            None,
            {"fields": ("reference", "type", "project", "timestamp")},
        ]
    ]


@admin.register(App)
class AppAdmin(
    ProjectLinkMixin,
    AdminConfirmMixin,
    ActionFormMixin,
    DjangoObjectActions,
    DynamicArrayMixin,
    admin.ModelAdmin,
):
    read_only_fields = ["last_seen"]

    list_display = [
        "reference",
        "get_event_status",
        "get_project",
        "last_seen",
        "default_sample_rate",
        "active_sample_rate",
        "active_window_end",
        "wsgi_collect_metrics",
        "celery_collect_metrics",
    ]

    search_fields = ["reference", "project__sentry_project_slug", "env", "command"]
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
            "Sentry",
            {
                "classes": ("collapse",),
                "fields": ("project", "env", "command"),
            },
        ],
        [
            "Metric - WSGI",
            {
                "classes": ("collapse",),
                "fields": (
                    "wsgi_collect_metrics",
                    "wsgi_ignore_path",
                    "wsgi_metrics",
                ),
            },
        ],
        [
            "Metric - Celery",
            {
                "classes": ("collapse",),
                "fields": (
                    "celery_collect_metrics",
                    "celery_ignore_task",
                    "celery_metrics",
                ),
            },
        ],
    ]
    actions = ["bump_sample_rate"]
    changelist_actions = ["panic", "unpanic"]
    change_actions = ["bump_sample_rate", "enable_disable_metrics"]

    inlines = [AppEventInline]

    @admin.display(description="Spamming Sentry")
    def get_event_status(self, obj):
        text = '<b style="color:{};">{}</b>'
        if obj.project and (event := obj.project.events.last()):
            if event.type == EventType.DISCARD:
                return format_html(text, "green", "No")
            return format_html(text, "red", "Yes")
        return format_html(text, "gray", "Pending")

    def get_changelist_actions(self, request):
        allowed_actions = []
        for action in self.changelist_actions:
            if getattr(self, f"has_{action}_permission")(request):
                allowed_actions.append(action)
        return allowed_actions

    def get_change_actions(self, request, object_id, form_url):
        allowed_actions = []
        for action in self.change_actions:
            if getattr(self, f"has_{action}_permission")(request):
                allowed_actions.append(action)
        return allowed_actions

    # ----- Bump Sample Rate
    @takes_instance_or_queryset
    @add_form_to_action(BumpForm)
    @confirm_action()
    @admin.action(description="Bump Sample Rate")
    def bump_sample_rate(self, request, queryset, form: BumpForm = None):  # pylint: disable=unused-argument
        new_date = timezone.now() + form.cleaned_data["duration"]
        queryset.update(
            active_sample_rate=form.cleaned_data["new_sample_rate"],
            active_window_end=new_date,
        )
        for app in queryset:
            invalidate_cache(f"/sentry/apps/{app.reference}/")

    bump_sample_rate.allowed_permissions = ("bump_sample_rate",)

    def has_bump_sample_rate_permission(self, request):
        """Does the user have the bump permission?"""
        opts = self.opts
        codename = get_permission_codename("bump_sample_rate", opts)

        panic = cache.get(settings.PANIC_KEY)
        return not panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

    # ----- Update Metrics
    @takes_instance_or_queryset
    @add_form_to_action(MetricForm)
    @admin.action(description="Enable/Disable Metrics Collection")
    def enable_disable_metrics(self, request, queryset, form: MetricForm = None):  # pylint: disable=unused-argument
        metrics = form.cleaned_data["metrics"]
        app: App
        for app in queryset:
            for metric in MetricType:
                app.set_metric(metric, metric.value in metrics)
            invalidate_cache(f"/sentry/apps/{app.reference}/")
            app.save()

    enable_disable_metrics.allowed_permissions = ("enable_disable_metrics",)

    def has_enable_disable_metrics_permission(self, request):
        """Does the user have the enable_disable_metrics permission?"""
        opts = self.opts
        codename = get_permission_codename("enable_disable_metrics", opts)

        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    # ----- Panic / Unpanic
    @takes_instance_or_queryset
    @confirm_action(display_queryset=False)
    @admin.action(description="Panic")
    def panic(self, request, queryset):  # pylint: disable=unused-argument
        cache.set(settings.PANIC_KEY, True, timeout=None)

    panic.allowed_permissions = ("panic",)
    panic.attrs = {"style": "background-color: red;"}

    def has_panic_permission(self, request):
        """Does the user have the panic permission?"""
        panic = cache.get(settings.PANIC_KEY)
        opts = self.opts
        codename = get_permission_codename("panic", opts)
        return not panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

    @takes_instance_or_queryset
    @confirm_action(display_queryset=False)
    @admin.action(description="UnPanic")
    def unpanic(self, request, queryset):  # pylint: disable=unused-argument
        cache.delete(settings.PANIC_KEY)

    unpanic.allowed_permissions = ("unpanic",)
    unpanic.attrs = {"style": "background-color: green;"}

    def has_unpanic_permission(self, request):
        """Does the user have the panic permission?"""
        panic = cache.get(settings.PANIC_KEY)
        opts = self.opts
        codename = get_permission_codename("panic", opts)
        return panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

    # Save model
    def save_model(self, request, obj, form, change) -> None:
        invalidate_cache(f"/sentry/apps/{obj.reference}/")
        return super().save_model(request, obj, form, change)
