"""Admin."""
from typing import TYPE_CHECKING, Optional

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
from controller.sentry.filters import IsSpammingListFilter
from controller.sentry.forms import BumpForm, MetricForm
from controller.sentry.inlines import AppEventInline, ProjectEventInline
from controller.sentry.mixins import ChartMixin, PrettyTypeMixin, ProjectLinkMixin
from controller.sentry.models import App, Event, Project
from controller.sentry.utils import invalidate_cache

if TYPE_CHECKING:  # pragma: no cover  # pragma: no cover
    from django.db.models import QuerySet
    from django.forms import ModelForm
    from django.http import HttpRequest


@admin.register(Project)
class ProjectAdmin(
    ChartMixin,
    DynamicArrayMixin,
    admin.ModelAdmin,
):
    """Project Admin."""

    list_display = [
        "sentry_id",
        "sentry_project_slug",
    ]

    search_fields = ["sentry_id", "sentry_project_slug"]
    ordering = search_fields

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget(width="100%")},
    }

    fieldsets = [
        [
            None,
            {
                "fields": (
                    "sentry_id",
                    "sentry_project_slug",
                    ("detection_param", "detection_result"),
                )
            },
        ]
    ]

    inlines = [ProjectEventInline]

    def get_chart_data(self, sentry_id):
        """This method return the chart data.

        Args:
            sentry_id (str): sentry id

        Returns:
            Optional[Tuple[dict, dict]]: tuple of data and options
        """
        project = Project.objects.get(sentry_id=sentry_id)
        if project.detection_result is None:
            return None

        threshold = project.detection_param["threshold"]

        options = {
            "aspectRatio": 4,
            "scales": {
                "xAxis": {"type": "timeseries"},
                "series": {"position": "left"},
                "signal": {"position": "right", "min": 0, "max": 2},
            },
            "plugins": {"legend": {"position": "bottom"}, "title": {"display": True, "text": "Detection Result"}},
            "elements": {"line": {"stepped": True}, "point": {"radius": 0}},
            "interaction": {"mode": "index", "intersect": False},
        }
        data = {
            "datasets": [
                {
                    "label": "Series",
                    "backgroundColor": "#36a2eb",
                    "borderColor": "#36a2eb",
                    "data": project.detection_result["series"],
                    "yAxisID": "series",
                },
                {
                    "label": "Signal",
                    "backgroundColor": "#ff6384",
                    "borderColor": "#ff6384",
                    "data": project.detection_result["signal"],
                    "yAxisID": "signal",
                },
                {
                    "label": "Threshold",
                    "backgroundColor": "#9966ff",
                    "borderColor": "#9966ff",
                    "data": [
                        avg_filter + threshold * std_filter
                        for avg_filter, std_filter in zip(
                            project.detection_result["avg_filter"],
                            project.detection_result["std_filter"],
                        )
                    ],
                    "yAxisID": "series",
                },
            ],
            "labels": project.detection_result["intervals"],
        }
        return data, options


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
    """Event Admin."""

    list_display = ["reference", "pretty_type", "timestamp", "get_project"]

    search_fields = ["reference", "type", "project__sentry_project_slug"]
    ordering = search_fields

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget(width="100%")},
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
    """App Admin."""

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

    list_filter = ["env", "command", IsSpammingListFilter]

    search_fields = ["reference", "project__sentry_project_slug", "env", "command"]
    ordering = search_fields

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget(width="100%")},
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
    def get_event_status(self, obj: App) -> str:
        """This method return a pretty event status html string.

        Args:
            obj (App): The app

        Returns:
            str: The pretty status
        """
        text = '<b style="color:{};">{}</b>'
        if obj.project and (event := obj.project.events.last()):
            if event.type == EventType.DISCARD:
                return format_html(text, "green", "No")
            return format_html(text, "red", "Yes")
        return format_html(text, "gray", "Pending")

    def get_changelist_actions(self, request: "HttpRequest") -> list[str]:
        """This method return allowed changelist actions.

        Args:
            request (HttpRequest): The request

        Returns:
            list[str]: All possible actions
        """
        allowed_actions = []
        for action in self.changelist_actions:
            if getattr(self, f"has_{action}_permission")(request):
                allowed_actions.append(action)
        return allowed_actions

    def get_change_actions(self, request: "HttpRequest", object_id: str, form_url: Optional[str]) -> list[str]:
        """This method return allowed change actions.

        Args:
            request (HttpRequest): The request
            object_id (str): The App reference
            form_url (Optional[str]): The form_url

        Returns:
            list[str]: All possible actions
        """
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
    def bump_sample_rate(
        self,
        request: "HttpRequest",
        queryset: "QuerySet[App]",
        form: BumpForm = None,  # pylint: disable=unused-argument
    ) -> None:
        """This method is responsible for the bump sample rate action.

        Args:
            request (HttpRequest): The request
            queryset (QuerySet[App]): The Apps to change
            form (BumpForm): The form
        """
        new_date = timezone.now() + form.cleaned_data["duration"]
        queryset.update(
            active_sample_rate=form.cleaned_data["new_sample_rate"],
            active_window_end=new_date,
        )
        for app in queryset:
            invalidate_cache(f"/sentry/apps/{app.reference}/")

    bump_sample_rate.allowed_permissions = ("bump_sample_rate",)

    def has_bump_sample_rate_permission(self, request: "HttpRequest") -> bool:
        """This method return True if the user have the permission for bump sample rate action.

        Args:
            request (HttpRequest): The request

        Returns:
            bool: Is allowed
        """
        opts = self.opts
        codename = get_permission_codename("bump_sample_rate", opts)

        panic = cache.get(settings.PANIC_KEY)
        return not panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

    # ----- Update Metrics
    @takes_instance_or_queryset
    @add_form_to_action(MetricForm)
    @admin.action(description="Enable/Disable Metrics Collection")
    def enable_disable_metrics(
        self,
        request: "HttpRequest",
        queryset: "QuerySet[App]",
        form: MetricForm = None,  # pylint: disable=unused-argument
    ) -> None:
        """This method is responsible for the enable/disable metrics action.

        Args:
            request (HttpRequest): The request
            queryset (QuerySet[App]): The Apps to change
            form (MetricForm): The form
        """
        metrics = form.cleaned_data["metrics"]
        app: App
        for app in queryset:
            for metric in MetricType:
                app.set_metric(metric, metric.value in metrics)
            invalidate_cache(f"/sentry/apps/{app.reference}/")
            app.save()

    enable_disable_metrics.allowed_permissions = ("enable_disable_metrics",)

    def has_enable_disable_metrics_permission(self, request: "HttpRequest") -> bool:
        """This method return True if the user have the permission for enable/disable metrics action.

        Args:
            request (HttpRequest): The request

        Returns:
            bool: Is allowed
        """
        opts = self.opts
        codename = get_permission_codename("enable_disable_metrics", opts)

        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    # ----- Panic / Unpanic
    @takes_instance_or_queryset
    @confirm_action(display_queryset=False)
    @admin.action(description="Panic")
    def panic(self, request: "HttpRequest", queryset: "QuerySet[App]") -> None:  # pylint: disable=unused-argument
        """This method activate the panic mode.

        Args:
            request (HttpRequest): The request
            queryset (QuerySet[App]): All the Apps (unused)
        """
        cache.set(settings.PANIC_KEY, True, timeout=None)

    panic.allowed_permissions = ("panic",)
    panic.attrs = {"style": "background-color: red;"}

    def has_panic_permission(self, request: "HttpRequest") -> bool:
        """This method return True if the user have the permission for panic action.

        Args:
            request (HttpRequest): The request

        Returns:
            bool: Is allowed
        """
        panic = cache.get(settings.PANIC_KEY)
        opts = self.opts
        codename = get_permission_codename("panic", opts)
        return not panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

    @takes_instance_or_queryset
    @confirm_action(display_queryset=False)
    @admin.action(description="UnPanic")
    def unpanic(self, request: "HttpRequest", queryset: "QuerySet[App]") -> None:  # pylint: disable=unused-argument
        """This method deactivate the panic mode.

        Args:
            request (HttpRequest): The request
            queryset (QuerySet[App]): All the Apps (unused)
        """
        cache.delete(settings.PANIC_KEY)

    unpanic.allowed_permissions = ("unpanic",)
    unpanic.attrs = {"style": "background-color: green;"}

    def has_unpanic_permission(self, request: "HttpRequest") -> bool:
        """This method return True if the user have the permission for unpanic action.

        Args:
            request (HttpRequest): The request

        Returns:
            bool: Is allowed
        """
        panic = cache.get(settings.PANIC_KEY)
        opts = self.opts
        codename = get_permission_codename("panic", opts)
        return panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

    # Save model
    def save_model(self, request: "HttpRequest", obj: App, form: "ModelForm", change: bool) -> None:
        """This method is responsible to save app in the admin.

        Args:
            request (HttpRequest): The request
            obj (App): The app to save
            form (ModelForm): form
            change (bool): change
        """
        invalidate_cache(f"/sentry/apps/{obj.reference}/")
        return super().save_model(request, obj, form, change)
