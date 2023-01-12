from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

DEVELOPER_GROUP = Group.objects.get(name=settings.DEVELOPER_GROUP)


class ControllerOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super().create_user(claims)
        self._set_username(user, claims)
        self._set_perms(user)
        user.save()

        return user

    def update_user(self, user, claims):
        self._set_username(user, claims)
        self._set_perms(user)
        user.save()

        return user

    def _set_username(self, user, claims):
        email = claims.get("email")
        username = email.split("@")[0]
        user.username = claims.get("preferred_username") or username
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")

    def _set_perms(self, user):
        user.is_staff = True
        user.groups.add(DEVELOPER_GROUP)
