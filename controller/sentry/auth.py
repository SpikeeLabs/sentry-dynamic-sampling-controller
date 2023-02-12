"""OIDC Auth."""
from functools import lru_cache
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth import get_user_model

    User = get_user_model()


@lru_cache
def get_group(group: str) -> Group:
    """get_group function is a cached helper to get a group from it's name.

    Args:
        group (str): The group name

    Returns:
        Group: The group
    """
    return Group.objects.get(name=group)


class ControllerOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """This class is responsible of the authentication."""

    def create_user(self, claims: dict) -> "User":
        """This method is responsible for the user creation.

        It create the user with the username and default permissions

        Args:
            claims (dict): OIDC claims

        Returns:
            User: The user
        """
        user = super().create_user(claims)
        self._set_username(user, claims)
        self._set_perms(user)
        user.save()

        return user

    def update_user(self, user: "User", claims: dict) -> "User":
        """This method is responsible for updating the user.

        Each times the user login we update his information

        Args:
            user (User): The user to update
            claims (dict): OIDC claims

        Returns:
            User: The new user
        """
        self._set_username(user, claims)
        self._set_perms(user)
        user.save()

        return user

    def _set_username(self, user: "User", claims: dict):
        """This method update the username of user from claim.

        Args:
            user (User): The user to update
            claims (dict): OIDC claims
        """
        email = claims.get("email")
        username = email.split("@")[0]
        user.username = claims.get("preferred_username") or username
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")

    def _set_perms(self, user: "User"):
        """This method update the permissions of user.

        Args:
            user (User): The user to update
        """
        user.is_staff = True
        user.groups.add(get_group(settings.DEVELOPER_GROUP))
