"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from knox.views import LogoutView, LogoutAllView

from .views import (
    UserViewSet,
    MeView,
    LogInView,
    ChangePasswordView,
    SendMailView,
    ResetPasswordView,
    CategoryView,
    SearchQueryView,
    VerificationView,
    SearchLicenseView,
    SendVerificationView,
    GetPhoneNumberVerificationCodeSMSView,
    GetPhoneNumberVerificationCodeCallView,
    PhoneNumberVerificationView,
    HelpDocumentationView,
    PendoView,
    TermsAndConditionAcceptanceView,
    ZohoPermissionsView,
    NewsletterSubscriptionViewSet,
)

app_name = "user"

router = SimpleRouter()
router.register(r'user', UserViewSet, base_name="user")
router.register(r'help-documentation', HelpDocumentationView, base_name="help-documentation")
router.register(r'newsletter-subscription', NewsletterSubscriptionViewSet, base_name="newsletter-subscription")

urlpatterns = [
    path(r'user/me/', MeView.as_view(), name='user-me'),
    # path(r'user/login/', LogInView.as_view(), name='login'),
    path(r'user/logout/', LogoutAllView.as_view(), name='logout'), #LogoutView - removes only single related token from DB.
    path(r'user/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path(r'user/forgot-password/', SendMailView.as_view(), name='forgot-password'),
    path(r'user/reset-password/', ResetPasswordView.as_view(), name='reset'),
    path(r'user/verify/', VerificationView.as_view(), name='verify-user'),
    path(r'user/send-verification/', SendVerificationView.as_view(), name='verification-user'),
    path(r'user/send-phone-verification-sms/', GetPhoneNumberVerificationCodeSMSView.as_view(), name='send-phone-verification-code-sms'),
    path(r'user/send-phone-verification-call/', GetPhoneNumberVerificationCodeCallView.as_view(), name='send-phone-verification-code-call'),
    path(r'user/phone-verify/', PhoneNumberVerificationView.as_view(), name='phone-verification'),
    path(r'category/', CategoryView.as_view(), name='category'),
    path(r'search/', SearchQueryView.as_view(), name='search'),
    path(r'search/licenses/', SearchLicenseView.as_view(), name='search-licenses'),
    path(r'terms-and-condition-acceptance/', TermsAndConditionAcceptanceView.as_view(), name='terms-and-condition-acceptance'),
    path(r'pendo/me/', PendoView.as_view(), name='pendo-me'),
    path(r'books/permission/', ZohoPermissionsView.as_view(), name="zoho-permission"),
] + router.urls
