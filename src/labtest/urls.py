"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
     LabTestViewSet,
     LabTestSyncViewSet,
)

app_name = "labtest"

router = SimpleRouter()
router.register(r'labtest', LabTestViewSet, base_name="labtest")

urlpatterns = [
     path(r'labtest/sync/', LabTestSyncViewSet.as_view(), name='sync_labtest'),
] + router.urls
