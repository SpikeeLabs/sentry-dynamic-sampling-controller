"""controller URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path, re_path, reverse
from django.views import View
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from controller.sentry import views

router = DefaultRouter()
router.register(r"apps", views.AppViewSet, basename="apps")


class CustomLogin(View):
    def get(self, request, **kwargs):  # pylint: disable=unused-argument
        url = reverse("oidc_authentication_init")
        return HttpResponseRedirect(url + ("?next={}".format(request.GET["next"]) if "next" in request.GET else ""))


urlpatterns = [
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("admin/login/", CustomLogin.as_view()),
    path("admin/", admin.site.urls),
    path("health/", include("health_check.urls")),
    path("sentry/", include((router.urls, "sentry"), namespace="sentry")),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]
