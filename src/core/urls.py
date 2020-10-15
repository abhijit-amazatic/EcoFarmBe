"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import (url, include,)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.static import serve
from knox.views import LogoutView
from rest_framework.routers import SimpleRouter
from user.views import (UserViewSet, MeView, LogInView,
                        ChangePasswordView, SendMailView,
                        ResetPasswordView, CategoryView,
                        SearchQueryView, VerificationView,
                        SendVerificationView,
                        GetPhoneNumberVerificationCodeSMSView,
                        GetPhoneNumberVerificationCodeCallView,
                        PhoneNumberVerificationView,)
from integration.views import (GetBoxTokensView, InventoryView,
                               GetPickListView, EstimateView,
                               ContactView, CRMContactView, SearchCultivars,
                               LeadView, GetBoxSharedLink, LeadSourcesView,
                               PurchaseOrderView, CRMVendorView,
                               VendorPaymentView, InvoiceView,
                               AccountSummaryView, VendorCreditView,
                               EstimateTaxView, GetTaxView,
                               ContactAddressView, GetPickListAccountView,
                               EstimateStatusView, ClientCodeView,
                               EstimateSignView, EstimateSignCompleteView,
                               GetDocumentStatus, GetSignURL,
                               TemplateSignView, GetDistanceView,
                               GetSalesPersonView, GetTemplateStatus,
                               CustomerPaymentView, GetBoxTokenAuthenticationView)
from inventory.views import (InventoryViewSet, InventorySyncView,
                             CultivarCategoryView, InventoryStatusTypeView,
                             ItemFeedbackViewSet, InventoryUpdateDateView,
                             InTransitOrderViewSet, DocumentPreSignedView,
                             DocumentView, DocumentStatusView, InventoryDeleteView)
from cultivar.views import (CultivarViewSet, CultivarSyncView, )
from labtest.views import (LabTestViewSet, LabTestSyncViewSet, )
from brand.views import (ProfileCategoryView, BrandViewSet, LicenseViewSet, KpiViewSet, ProfileReportViewSet, FileUploadView)
from two_factor.views import (
    TwoFactorLoginEnableView,
    TwoFactorLoginDisableView,
    TwoFactoLogInViewSet,
    AuthyAddUserRequestViewSet,
    AuthyOneTouchRequestCallbackView,
    AuthyUserRegistrationCallbackView,
    TwoFactorDeviceViewSet,
    AddPhoneDeviceViewSet,
)
router = SimpleRouter()
router.register(r'user/login', TwoFactoLogInViewSet, base_name="login-2fa")
router.register(r'user', UserViewSet, base_name="user")
router.register(r'inventory', InventoryViewSet, base_name="inventory")
router.register(r'item-feedback', ItemFeedbackViewSet, base_name="feedback")
router.register(r'cultivar', CultivarViewSet, base_name="cultivar")
router.register(r'labtest', LabTestViewSet, base_name="labtest")
router.register(r'brand', BrandViewSet, base_name="brand")
router.register(r'license', LicenseViewSet, base_name="license")
router.register(r'profile-report', ProfileReportViewSet, base_name="report")
router.register(r'in-transit-order', InTransitOrderViewSet, base_name="in_transit_order")
router.register(r'two-factor/device', TwoFactorDeviceViewSet, base_name="two-factor-device")
router.register(r'two-factor/add-device/authy-one-touch', AuthyAddUserRequestViewSet, base_name="add-authy-user")
router.register(r'two-factor/add-device/phone', AddPhoneDeviceViewSet, base_name="add-phone-device")




urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'user/me/', MeView.as_view(), name='user-me'),
    # path(r'user/login/', LogInView.as_view(), name='login'),
    path(r'user/logout/', LogoutView.as_view(), name='logout'),
    path(r'user/change-password/',
         ChangePasswordView.as_view(), name='change-password'),
    path(r'user/forgot-password/', SendMailView.as_view(), name='forgot-password'),
    path(r'user/reset-password/', ResetPasswordView.as_view(), name='reset'),
    path(r'user/verify/', VerificationView.as_view(), name='verify-user'),
    path(r'user/send-verification/', SendVerificationView.as_view(), name='verification-user'),
    path(r'user/send-phone-verification-sms/', GetPhoneNumberVerificationCodeSMSView.as_view(), name='send-phone-verification-code-sms'),
    path(r'user/send-phone-verification-call/', GetPhoneNumberVerificationCodeCallView.as_view(), name='send-phone-verification-code-call'),
    path(r'user/phone-verify/', PhoneNumberVerificationView.as_view(), name='phone-verification'),
    path(r'two-factor/authy-callback/one-touch-request/', AuthyOneTouchRequestCallbackView.as_view(), name='authy-one-touch-request-callback'),
    path(r'two-factor/authy-callback/user-registration/', AuthyUserRegistrationCallbackView.as_view(), name='authy-user-registration-callback'),
    path(r'two-factor/enable-2fa-login/', TwoFactorLoginEnableView.as_view(), name='enable-2fa-login'),
    path(r'two-factor/disable-2fa-login/', TwoFactorLoginDisableView.as_view(), name='enable-2fa-login'),
    path(r'category/', CategoryView.as_view(), name='category'),
    path(r'search/', SearchQueryView.as_view(), name='search'),
    path(r'box/link/', GetBoxSharedLink.as_view(), name='get_shared_link'),
    path(r'integration/box/', GetBoxTokensView.as_view(), name='box'),
    path(r'integration/box-aws/',
         GetBoxTokenAuthenticationView.as_view(), name='box-token-authentication'),
    path(r'crm/search/cultivar', SearchCultivars.as_view(), name='search_cultivar'),
    path(r'crm/picklist/', GetPickListView.as_view(), name='get_picklist'),
    path(r'crm/account-picklist/', GetPickListAccountView.as_view(),
         name='get_account_picklist'),
    path(r'crm/contact/', CRMContactView.as_view(), name='list_crm_contacts'),
    path(r'crm/lead/', LeadView.as_view(), name='create_lead'),
    path(r'crm/lead-sources/', LeadSourcesView.as_view(), name='get_lead_sources'),
    path(r'crm/vendor/', CRMVendorView.as_view(), name='get_vendor'),
    path(r'crm/account-client-code/', ClientCodeView.as_view(),
         name='get_account_client_code'),
    path(r'cultivar/sync/', CultivarSyncView.as_view(), name='sync_cultivar'),
    path(r'books/estimate/', EstimateView.as_view(), name='estimate'),
    path(r'books/contact/', ContactView.as_view(), name='contact'),
    path(r'books/contact-address/',
         ContactAddressView.as_view(), name='contact_address'),
    path(r'books/purchase-order/',
         PurchaseOrderView.as_view(), name='purchase_order'),
    path(r'books/vendor-payment/',
         VendorPaymentView.as_view(), name='vendor_payment'),
    path(r'books/customer-payment/',
         CustomerPaymentView.as_view(), name='customer_payment'),
    path(r'books/invoice/', InvoiceView.as_view(), name='invoices'),
    path(r'books/vendor-credits/',
         VendorCreditView.as_view(), name='vendor_credits'),
    path(r'books/account-summary/',
         AccountSummaryView.as_view(), name='account_summary'),
    path(r'books/calculate-tax/', EstimateTaxView.as_view(), name='calculate-tax'),
    path(r'books/tax/', GetTaxView.as_view(), name='get-tax'),
    path(r'books/estimate-status/',
         EstimateStatusView.as_view(), name='update_status'),
    path(r'books/sign-estimate/', EstimateSignView.as_view(), name='sign-estimate'),
    path(r'books/signed-estimate/',
         EstimateSignCompleteView.as_view(), name='sined-estimate'),
    path(r'books/sign-status/', GetDocumentStatus.as_view(), name='get-sign-status'),
    path(r'books/sign-url/', GetSignURL.as_view(), name='get-sign-url'),
    path(r'inventory/sync', InventorySyncView.as_view(), name='sync_inventory'),
    path(r'inventory/cultivar', CultivarCategoryView.as_view(),
         name='cultivar_category'),
    path(r'inventory/status/', InventoryStatusTypeView.as_view(),
         name='get_status_types'),
    path(r'inventory/last-modified-time/',
         InventoryUpdateDateView.as_view(), name='get_last_modified_time'),
    path(r'delete-item/<str:item_id>/',
         InventoryDeleteView.as_view(), name='delete_inventory'),
    path(r'labtest/sync/', LabTestSyncViewSet.as_view(), name='sync_labtest'),
    path(r'sign/template/', TemplateSignView.as_view(), name='sign_template'),
    path(r'sign/template-status/',
         GetTemplateStatus.as_view(), name='template_status'),
    path(r'integration/distance/', GetDistanceView.as_view(), name='get_distance'),
    path(r'crm/sales-person/', GetSalesPersonView.as_view(),
         name='get_sales_person'),
    path(r'profile-category/', ProfileCategoryView.as_view(), name='category'),
    path(r'platform-kpi/', KpiViewSet.as_view(), name='kpi'),
    path(r'file-upload/', FileUploadView.as_view(), name='file-upload'),
    path(r'document-url/<str:id>/', DocumentPreSignedView.as_view(), name='documents-url'),
    path(r'document-url/', DocumentPreSignedView.as_view(), name='documents-url'),
    path(r'document-status/<str:id>/', DocumentStatusView.as_view(), name='extra-documents'),
    path(r'document/', DocumentView.as_view(), name='extra-documents'),
    path(r'document/<str:id>/', DocumentView.as_view(), name='extra-documents')
] + router.urls


if not settings.DEBUG:
    urlpatterns += [
        url(r'^static\/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT})
    ]
