from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.admin.sites import site as default_site
from django.contrib.auth.models import Group
from undecorated import undecorated

from controller.sentry.admin import AppAdmin
from controller.sentry.forms import BumpForm
from controller.sentry.models import App


class MockRequest:
    def __init__(self, user) -> None:
        self.user = user


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
        ("Owner", False, ["bump_sample_rate"]),
        ("Admin", False, ["bump_sample_rate"]),
        ("Developer", False, ["bump_sample_rate"]),
        ("Viewer", False, []),
        ("Owner", True, []),
        ("Admin", True, []),
        ("Developer", True, []),
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
