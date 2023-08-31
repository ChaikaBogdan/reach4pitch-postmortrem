"""reach4pitch URL Configuration

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
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from django.contrib.flatpages.sitemaps import FlatPageSitemap
from django.urls import include, path
from backend.models import Pitch, Publisher
from backend.views import (
    UserSignup,
    UserResetPassword,
    EmailActivate,
    EmailCollect,
    UploadImage,
)


pitches_info = {
    "queryset": Pitch.objects.filter(is_published=True).order_by("-created_at").all(),
    "date_field": "created_at",
}

publishers_info = {
    "queryset": Publisher.objects.order_by("-created_at").all(),
    "date_field": "created_at",
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("backend.urls")),
    path(
        "accounts/signup/",
        UserSignup.as_view(),
        name="signup",
    ),
    path(
        "accounts/activate/<str:uidb64>/<str:token>/",
        EmailActivate.as_view(),
        name="activate_email",
    ),
    path(
        "accounts/collect/",
        EmailCollect.as_view(),
        name="collect_email",
    ),
    path("accounts/password_reset/", UserResetPassword.as_view()),
    path("accounts/", include("django.contrib.auth.urls")),
    path("pages/", include("django.contrib.flatpages.urls")),
    path("captcha/", include("captcha.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {
            "sitemaps": {
                "pitch": GenericSitemap(pitches_info, priority=1.0),
                "publisher": GenericSitemap(publishers_info, priority=0.7),
                "flatpages": FlatPageSitemap,
            },
        },
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("django-rq/", include("django_rq.urls")),
    path("tinymce/upload_image/", UploadImage.as_view()),
    path("tinymce/", include("tinymce.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
