"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from fee_variable.views import (
    OrderVariableView,
    CustomInventoryVariableView,
    TaxVariableVariableView,
    ProgramViewSet,
    FileLinkViewSet,
)

app_name = "fee_variable"

router = SimpleRouter()
router.register(r'order-variables', OrderVariableView, base_name="order-variables")
router.register(r'inventory-variables', CustomInventoryVariableView, base_name="inventory-variables")
router.register(r'tax-variables', TaxVariableVariableView, base_name="tax-variables")
router.register(r'fee_variables/program', ProgramViewSet, base_name="Program")
router.register(r'fee_variables/file-link', FileLinkViewSet, base_name="file-link")

urlpatterns = [
    #path(r'order-variables/', OrderVariableView.as_view(), name='order-variables'),
] + router.urls
