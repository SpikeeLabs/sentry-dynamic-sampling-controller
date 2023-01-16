import pytest
from django.conf import settings

from controller.sentry.auth import ControllerOIDCAuthenticationBackend, get_group


@pytest.mark.django_db
def test_auth_controller():
    auth = ControllerOIDCAuthenticationBackend()
    claims = {
        "email": "test@spikeelab.fr",
    }
    user = auth.create_user(claims)
    assert user.username == "test"
    assert user.first_name == ""
    assert user.last_name == ""

    assert user.groups.count() == 1
    assert user.groups.all()[0] == get_group(settings.DEVELOPER_GROUP)

    claims = {
        "email": "test@spikeelab.fr",
        "preferred_username": "test_user",
        "given_name": "toto",
        "family_name": "tata",
    }

    user = auth.update_user(user, claims)
    assert user.username == "test_user"
    assert user.first_name == "toto"
    assert user.last_name == "tata"
