"""
URL Configuration
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    EstimateWebappView,
)

app_name = "bill"

router = SimpleRouter()

urlpatterns = [
    path(r'books/estimate/sales-rep/', EstimateWebappView.as_view(), name="estimate-sales-rep-view"),
    path(r'books/estimate/sales-rep/<str:id>/', EstimateWebappView.as_view(), name="estimate-sales-rep-view"),
] + router.urls
