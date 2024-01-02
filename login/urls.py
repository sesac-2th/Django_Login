from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg       import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="django-login",
        default_version='1.0.0',
        description="django-login",
        terms_of_service="",
        contact=openapi.Contact(email="juhwan@woongpang.com"), 
        license=openapi.License(name="juhwan"), 
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path(r'swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(r'redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-v1'),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
]