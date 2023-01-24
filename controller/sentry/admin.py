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
        "sentry_project_slug",
        "last_seen",
        "default_sample_rate",
        "active_sample_rate",
        "active_window_end",
        "wsgi_collect_metrics",
        "celery_collect_metrics",
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
            "Sentry",
            {
                "classes": ("collapse", "open"),
                "fields": ("sentry_project_slug",),
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
    actions = ["bump_sample_rate"]
    changelist_actions = ["panic", "unpanic"]
    change_actions = ["bump_sample_rate"]

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

    bump_sample_rate.allowed_permissions = ("bump_sample_rate",)

    def has_bump_sample_rate_permission(self, request):
        """Does the user have the bump permission?"""
        opts = self.opts
        codename = get_permission_codename("bump_sample_rate", opts)

        panic = cache.get(settings.PANIC_KEY)
        return not panic and request.user.has_perm("%s.%s" % (opts.app_label, codename))

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

    def save_model(self, request, obj, form, change) -> None:
        invalidate_cache(f"/sentry/apps/{obj.reference}/")
        return super().save_model(request, obj, form, change)
