"""
URL Configuration
"""
from django.conf.urls import (
    url,
    include,
)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.static import serve
from knox.views import LogoutView, LogoutAllView
from rest_framework.routers import SimpleRouter

from .views import (
    TwoFactorLoginEnableView,
    TwoFactorLoginDisableView,
    TwoFactoLogInViewSet,
    AuthyAddUserRequestViewSet,
    AuthyOneTouchRequestCallbackView,
    AuthyUserRegistrationCallbackView,
    TwoFactorDeviceViewSet,
    AddPhoneDeviceViewSet,
    AddAuthenticatorRequestViewSet,
)

app_name = "two_factor"

router = SimpleRouter()
router.register(r'user/login', TwoFactoLogInViewSet, base_name="login-2fa")
router.register(r'two-factor/device', TwoFactorDeviceViewSet, base_name="two-factor-device")
router.register(r'two-factor/add-device/authy-one-touch', AuthyAddUserRequestViewSet, base_name="add-authy-user")
router.register(r'two-factor/add-device/phone', AddPhoneDeviceViewSet, base_name="add-phone-device")
router.register(r'two-factor/add-device/authenticator', AddAuthenticatorRequestViewSet, base_name="add-authenticator-device")

urlpatterns = [
    path(r'two-factor/authy-callback/one-touch-request/', AuthyOneTouchRequestCallbackView.as_view(), name='authy-one-touch-request-callback'),
    path(r'two-factor/authy-callback/user-registration/', AuthyUserRegistrationCallbackView.as_view(), name='authy-user-registration-callback'),
    path(r'two-factor/enable-2fa-login/', TwoFactorLoginEnableView.as_view(), name='enable-2fa-login'),
    path(r'two-factor/disable-2fa-login/', TwoFactorLoginDisableView.as_view(), name='enable-2fa-login'),

] + router.urls
