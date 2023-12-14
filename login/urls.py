from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework import permissions




urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
]