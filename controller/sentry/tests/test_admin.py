from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.admin.sites import site as default_site
from django.contrib.auth.models import Group
from django.utils import timezone
from undecorated import undecorated

from controller.sentry.admin import AppAdmin
from controller.sentry.choices import EventType
from controller.sentry.filters import IsSpammingListFilter
from controller.sentry.forms import BumpForm, MetricForm
from controller.sentry.inlines import AppEventInline, ProjectEventInline
from controller.sentry.models import App, Event, Project


class MockRequest:
    def __init__(self, user) -> None:
        self.user = user
        self.META = {}
        self.method = "GET"
        self.COOKIES = {}
        self.POST = {}
        self.GET = {}


class MockResponse:
    def __init__(self, context_data=None) -> None:
        if context_data:
            self.context_data = {}


@pytest.fixture
def user_with_group(request, django_user_model, user_group):
    marker = request.node.get_closest_marker("user_group")
    if not marker and not user_group:
        raise ValueError("No user_group passed")

    group_name = marker.args[0] if marker else user_group
    group = Group.objects.get(name=group_name)

    user = django_user_model.objects.create_user(username="test", password="test")
    user.groups.set([group])
    return user


@pytest.fixture
def client_with_user(client, user_with_group):

    client.force_login(user_with_group)

    return client


@pytest.fixture
def admin_with_user(request, user_with_group):
    marker = request.node.get_closest_marker("admin_site")
    if not marker:
        raise ValueError("No admin_site passed")

    model_class = marker.kwargs["model_class"]

    admin_site = default_site._registry[model_class]

    return admin_site, MockRequest(user_with_group)


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_group,panic,expected",
    [
        ("Owner", False, True),
        ("Admin", False, True),
        ("Developer", False, True),
        ("Viewer", False, False),
        ("Owner", True, False),
        ("Admin", True, False),
        ("Developer", True, False),
        ("Viewer", True, False),
    ],
)
@pytest.mark.admin_site(model_class=App)
def test_app_admin_has_bump_perm(
    cache: Mock, request, admin_with_user: tuple[AppAdmin, MockRequest], expected: bool, panic: bool
):
    site, request = admin_with_user
    cache.get.return_value = panic
    assert site.has_bump_sample_rate_permission(request) == expected


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_group,panic,expected",
    [
        ("Owner", False, True),
        ("Admin", False, True),
        ("Developer", False, False),
        ("Viewer", False, False),
        ("Owner", True, False),
        ("Admin", True, False),
        ("Developer", True, False),
        ("Viewer", True, False),
    ],
)
@pytest.mark.admin_site(model_class=App)
def test_app_admin_has_panic_perm(
    cache: Mock, request, admin_with_user: tuple[AppAdmin, MockRequest], expected: bool, panic: bool
):
    site, request = admin_with_user
    cache.get.return_value = panic
    assert site.has_panic_permission(request) == expected


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_group,panic,expected",
    [
        ("Owner", False, False),
        ("Admin", False, False),
        ("Developer", False, False),
        ("Viewer", False, False),
        ("Owner", True, True),
        ("Admin", True, True),
        ("Developer", True, False),
        ("Viewer", True, False),
    ],
)
@pytest.mark.admin_site(model_class=App)
def test_app_admin_has_unpanic_perm(
    cache: Mock, request, admin_with_user: tuple[AppAdmin, MockRequest], expected: bool, panic: bool
):
    site, request = admin_with_user
    cache.get.return_value = panic
    assert site.has_unpanic_permission(request) == expected


@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_bump(request, admin_with_user):
    app = App(reference="test", active_sample_rate=0.1, active_window_end=None)
    app.save()
    form = BumpForm(
        {
            "new_sample_rate": 0.5,
            "duration_0": 0,
            "duration_1": 5,
        }
    )

    assert form.is_valid()
    site, request = admin_with_user
    bump_sample_rate = undecorated(site.bump_sample_rate)
    bump_sample_rate(site, request, App.objects.filter(reference=app.reference), form=form)
    app.refresh_from_db()
    assert app.active_sample_rate == 0.5
    assert app.active_window_end is not None


@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_metrics(request, admin_with_user):
    app = App(wsgi_collect_metrics=False, celery_collect_metrics=False)
    app.save()
    form = MetricForm({"metrics": ["WSGI", "CELERY"]})

    assert form.is_valid()
    site, request = admin_with_user
    enable_disable_metrics = undecorated(site.enable_disable_metrics)
    enable_disable_metrics(site, request, App.objects.filter(reference=app.reference), form=form)
    app.refresh_from_db()
    assert app.wsgi_collect_metrics
    assert app.celery_collect_metrics

    form = MetricForm({"metrics": []})
    assert form.is_valid()
    site, request = admin_with_user
    enable_disable_metrics = undecorated(site.enable_disable_metrics)
    enable_disable_metrics(site, request, App.objects.filter(reference=app.reference), form=form)
    app.refresh_from_db()
    assert not app.wsgi_collect_metrics
    assert not app.celery_collect_metrics

    form = MetricForm({"metrics": ["WSGI"]})
    assert form.is_valid()
    site, request = admin_with_user
    enable_disable_metrics = undecorated(site.enable_disable_metrics)
    enable_disable_metrics(site, request, App.objects.filter(reference=app.reference), form=form)
    app.refresh_from_db()
    assert app.wsgi_collect_metrics
    assert not app.celery_collect_metrics


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_panic(cache: Mock, admin_with_user):
    site, request = admin_with_user
    panic = undecorated(site.panic)
    panic(site, request, {})

    cache.set.assert_called_once_with(settings.PANIC_KEY, True, timeout=None)


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_unpanic(cache: Mock, admin_with_user):
    site, request = admin_with_user
    unpanic = undecorated(site.unpanic)
    unpanic(site, request, {})

    cache.delete.assert_called_once_with(settings.PANIC_KEY)


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_group,panic,result",
    [
        ("Owner", False, ["panic"]),
        ("Admin", False, ["panic"]),
        ("Developer", False, []),
        ("Viewer", False, []),
        ("Owner", True, ["unpanic"]),
        ("Admin", True, ["unpanic"]),
        ("Developer", True, []),
        ("Viewer", True, []),
    ],
)
@pytest.mark.admin_site(model_class=App)
def test_app_admin_get_changelist_actions(cache: Mock, admin_with_user, result, panic):
    site, request = admin_with_user
    cache.get.return_value = panic
    assert site.get_changelist_actions(request) == result


@patch("controller.sentry.admin.cache")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_group,panic,result",
    [
        ("Owner", False, ["bump_sample_rate", "enable_disable_metrics"]),
        ("Admin", False, ["bump_sample_rate", "enable_disable_metrics"]),
        ("Developer", False, ["bump_sample_rate", "enable_disable_metrics"]),
        ("Viewer", False, []),
        ("Owner", True, ["enable_disable_metrics"]),
        ("Admin", True, ["enable_disable_metrics"]),
        ("Developer", True, ["enable_disable_metrics"]),
        ("Viewer", True, []),
    ],
)
@pytest.mark.admin_site(model_class=App)
def test_app_admin_get_change_actions(cache: Mock, admin_with_user, result, panic):
    site, request = admin_with_user
    cache.get.return_value = panic
    assert site.get_change_actions(request, None, None) == result


@patch("controller.sentry.admin.invalidate_cache")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_save_model(invalidate_cache: Mock, admin_with_user):
    site, request = admin_with_user
    app = App(reference="test")
    site.save_model(request, app, None, None)
    invalidate_cache.assert_called_once_with("/sentry/apps/test/")


@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_get_project(admin_with_user):
    site, request = admin_with_user
    project = Project(sentry_id="123")
    app = App(reference="abc", project=project)
    assert site.get_project(app) == f'<a href="/admin/sentry/project/123/change/">{str(project)}</a>'


@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_admin_get_project_no_project(admin_with_user):
    site, request = admin_with_user
    app = App(reference="abc")
    assert site.get_project(app) is None


@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_get_event_status(admin_with_user):
    site, request = admin_with_user
    app = App(reference="abc")
    assert site.get_event_status(app) == '<b style="color:gray;">Pending</b>'

    app = App(reference="abc", project=Project(sentry_id="123"))
    assert site.get_event_status(app) == '<b style="color:gray;">Pending</b>'

    project = Project(sentry_id="123")
    project.save()
    event = Event(project=project, type=EventType.DISCARD, timestamp=timezone.now())
    event.save()
    app = App(reference="abc", project=project)
    assert site.get_event_status(app) == '<b style="color:green;">No</b>'

    project = Project(sentry_id="123")
    project.save()
    event = Event(project=project, type=EventType.FIRING, timestamp=timezone.now())
    event.save()
    app = App(reference="abc", project=project)
    assert site.get_event_status(app) == '<b style="color:red;">Yes</b>'


@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_get_app_status(admin_with_user):
    site, request = admin_with_user
    app = App(reference="abc", last_seen=timezone.now())
    assert site.get_active_status(app) == True

    app = App(reference="abc", last_seen=None)
    assert site.get_active_status(app) == False

    app = App(reference="abc", last_seen=timezone.now() - timedelta(minutes=60))
    assert site.get_active_status(app) == False


@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=Project)
def test_project_event_inlines(admin_with_user):
    site, request = admin_with_user
    inline = ProjectEventInline(Project, site.admin_site)
    assert not inline.has_add_permission({})
    assert not inline.has_change_permission({})

    project = Project(sentry_id="123")
    event = Event(project=project, type=EventType.FIRING, timestamp=timezone.now())

    assert inline.pretty_type(event) == '<b style="color:red;">Firing</b>'

    event = Event(project=project, type=EventType.DISCARD, timestamp=timezone.now())

    assert inline.pretty_type(event) == '<b style="color:green;">Discard</b>'


@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_event_inlines(admin_with_user):
    site, request = admin_with_user
    inline = AppEventInline(App, site.admin_site)
    app = App(reference="123")
    assert not inline.has_add_permission({})
    assert not inline.has_change_permission({})
    assert len(inline.get_form_queryset(app)) == 0

    project = Project(sentry_id="123")
    project.save()
    event = Event(project=project, type=EventType.FIRING, timestamp=timezone.now())
    event.save()
    app = App(reference="abc", project=project)
    assert len(inline.get_form_queryset(app)) == 1

    with pytest.raises(NotImplementedError):
        inline.save_new_instance({}, {})


@patch("django.contrib.admin.ModelAdmin.change_view")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=Project)
def test_project_chart_no_data(super_call: Mock, admin_with_user):
    site, request = admin_with_user
    project = Project(sentry_id="123")
    project.save()
    extra_context = object()
    site.change_view(request, project.sentry_id, extra_context=extra_context)

    super_call.assert_called_once_with(request, project.sentry_id, "", extra_context)


@patch("django.contrib.admin.ModelAdmin.change_view")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=Project)
def test_project_chart_no_context(super_call: Mock, admin_with_user):
    site, request = admin_with_user
    project = Project(sentry_id="123")
    project.detection_result = {
        "signal": [0, 1],
        "avg_filter": [0, 1],
        "std_filter": [0, 2],
        "series": [0, 5],
        "intervals": ["a", "b"],
    }
    project.save()
    super_call.return_value = MockResponse(context_data=False)
    response = site.change_view(request, project.sentry_id)
    assert not hasattr(response, "context_data")


@patch("django.contrib.admin.ModelAdmin.change_view")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=Project)
def test_project_chart(super_call: Mock, admin_with_user):
    site, request = admin_with_user
    project = Project(sentry_id="123")
    project.detection_result = [
        ("a", 0, 0, 0, 0),
        ("b", 55, 1, 1, 2),
    ]
    project.save()
    super_call.return_value = MockResponse(context_data=True)
    response = site.change_view(request, project.sentry_id)

    expected_context = {
        "adminchart_chartjs_config": {
            "type": "line",
            "data": {
                "datasets": [
                    {
                        "label": "Series",
                        "backgroundColor": "#36a2eb",
                        "borderColor": "#36a2eb",
                        "data": (0, 55),
                        "yAxisID": "series",
                    },
                    {
                        "label": "Signal",
                        "backgroundColor": "#ff6384",
                        "borderColor": "#ff6384",
                        "data": (0, 1),
                        "yAxisID": "signal",
                    },
                    {
                        "label": "Threshold",
                        "backgroundColor": "#9966ff",
                        "borderColor": "#9966ff",
                        "data": [50, 50],
                        "yAxisID": "series",
                    },
                ],
                "labels": ("a", "b"),
            },
            "options": settings.DEFAULT_GRAPH_OPTION,
        }
    }

    super_call.assert_called_once_with(request, project.sentry_id, "", None)

    assert response.context_data == expected_context


@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=App)
def test_app_filter(admin_with_user):
    site, request = admin_with_user

    project = Project.objects.create(sentry_id="123")
    event = Event.objects.create(project=project, type=EventType.DISCARD, timestamp=timezone.now())
    project.last_event = event
    project.save()
    app_discard = App.objects.create(reference="app_discard", project=project)

    project = Project.objects.create(sentry_id="456")
    event = Event.objects.create(project=project, type=EventType.FIRING, timestamp=timezone.now())
    project.last_event = event
    project.save()
    app_firing = App.objects.create(reference="app_firing", project=project)

    App.objects.create(reference="app_without")

    filter_yes = IsSpammingListFilter(None, {"spamming": "yes"}, App, site)
    filter_no = IsSpammingListFilter(None, {"spamming": "no"}, App, site)
    filter_none = IsSpammingListFilter(None, {}, App, site)

    assert filter_yes.lookups(request, site) == (("yes", "Yes"), ("no", "No"))

    assert list(filter_yes.queryset(request, App.objects.all())) == list(
        App.objects.filter(reference=app_firing.reference)
    )

    assert list(filter_no.queryset(request, App.objects.all())) == list(
        App.objects.filter(reference=app_discard.reference)
    )

    assert list(filter_none.queryset(request, App.objects.all())) == list(App.objects.all())


@patch("controller.sentry.admin.perform_detect")
@pytest.mark.django_db
@pytest.mark.parametrize("user_group", ["Developer"])
@pytest.mark.admin_site(model_class=Project)
def test_project_admin_save_model(perform_detect: Mock, admin_with_user):
    site, request = admin_with_user
    project = Project(sentry_id="test_project")
    site.save_model(request, project, None, True)
    perform_detect.delay.assert_called_once_with(project.sentry_id)

    perform_detect.reset_mock()
    site.save_model(request, project, None, None)
    perform_detect.delay.assert_not_called()
