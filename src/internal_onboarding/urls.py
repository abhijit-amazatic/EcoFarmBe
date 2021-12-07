"""
URL Configuration
"""
from django.conf.urls import (url, include,)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
     InternalOnboardingView,
)

app_name = 'internal_onboarding'

router = SimpleRouter()
router.register(r'internal-onboarding', InternalOnboardingView, base_name="internal-onboarding")

urlpatterns = [
] + router.urls
