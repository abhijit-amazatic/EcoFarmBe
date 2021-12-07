"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import(
     BinderLicenseViewSet,
)

app_name = "compliance_binder"

router = SimpleRouter()
router.register(r'compliance-binder/license', BinderLicenseViewSet, base_name="binder-license")

urlpatterns = [
] + router.urls
