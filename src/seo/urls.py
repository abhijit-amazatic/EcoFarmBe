"""
SEO URL Configuration
"""
from django.conf.urls import (url, include,)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.static import serve
from knox.views import LogoutView, LogoutAllView
from rest_framework.routers import SimpleRouter

from .views import (
    PageMetaViewSet,
)

app_name = 'seo'

router = SimpleRouter()
router.register(r'page-meta', PageMetaViewSet, base_name="page-meta")

urlpatterns = [
] + router.urls
