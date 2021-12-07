"""
URL Configuration
"""
from django.conf.urls import (url, include)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    OrganizationViewSet,
    ProfileCategoryView,
    BrandViewSet,
    LicenseViewSet,
    KpiViewSet,
    ProfileReportViewSet,
    FileUploadView,
    LicenseSyncView,
    OrganizationRoleViewSet,
    OrganizationUserViewSet,
    OrganizationUserRoleViewSet,
    InviteUserViewSet,
    UserInvitationVerificationView,
    ProgramSelectionSyncView,
    CultivarsOfInterestSyncView,
    OnboardingDataFetchViewSet,
    MyOrganizationRoleView,
)

app_name = "brand"

router = SimpleRouter()
router.register(r'organization', OrganizationViewSet, base_name="organization")
router.register(r'license', LicenseViewSet, 'license-all')

router.registry.extend([
    ('organization/(?P<parent_organization>[^/.]+)/brand', BrandViewSet, 'brand'),
    ('organization/(?P<parent_organization>[^/.]+)/license', LicenseViewSet, 'license'),
    ('organization/(?P<parent_organization>[^/.]+)/role', OrganizationRoleViewSet, 'organization-role'),
    ('organization/(?P<parent_organization>[^/.]+)/user', OrganizationUserViewSet, 'organization-user'),
    ('organization/(?P<parent_organization>[^/.]+)/user/(?P<parent_organization_user>[^/.]+)/role', OrganizationUserRoleViewSet, 'organization-user-role-nest'),
    ('organization/(?P<parent_license__organization>[^/.]+)/invite-user', InviteUserViewSet, 'organization-invite-user'),
])

router.register(r'profile-report', ProfileReportViewSet, base_name="report")
router.register(r'onboarding-data-fetch', OnboardingDataFetchViewSet, base_name="onboarding-data-fetch")

urlpatterns = [
    path(r'profile-category/', ProfileCategoryView.as_view(), name='category'),
    path(r'platform-kpi/', KpiViewSet.as_view(), name='kpi'),
    path('organization/<int:parent_organization>/platform-kpi/', KpiViewSet.as_view(), name='organization-kpi'),
    path('organization/<int:parent_organization>/my-permissions/', MyOrganizationRoleView.as_view(), name='my-permissions'),
    path(r'file-upload/', FileUploadView.as_view(), name='file-upload'),
    path(r'license/sync/', LicenseSyncView.as_view(), name='license-sync'),
    path(r'user-invitation-verify/', UserInvitationVerificationView.as_view(), name="user-invitation-verify"),
    path(r'update-program-selection/', ProgramSelectionSyncView.as_view(), name="update-program"),
    path(r'update-account-cultivars-of-interest/', CultivarsOfInterestSyncView.as_view(), name="update-account-cultivars-of-interest"),
] + router.urls
