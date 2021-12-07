"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
     PermissionListView,
)

app_name = "permission"

router = SimpleRouter()

urlpatterns = [
    path(r'permission-list/', PermissionListView.as_view(), name="permission-list"),
] + router.urls
