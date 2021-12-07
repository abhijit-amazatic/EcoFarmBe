"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    CultivarViewSet,
    CultivarSyncView,
)

app_name = "cultivar"

router = SimpleRouter()
router.register(r'cultivar', CultivarViewSet, base_name="cultivar")

urlpatterns = [
    path(r'cultivar/sync/', CultivarSyncView.as_view(), name='sync_cultivar'),
] + router.urls
