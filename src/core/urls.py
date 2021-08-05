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
from knox.views import LogoutView, LogoutAllView
from rest_framework.routers import SimpleRouter
from user.views import (UserViewSet, MeView, LogInView,
                        ChangePasswordView, SendMailView,
                        ResetPasswordView, CategoryView,
                        SearchQueryView, VerificationView,
                        SearchLicenseView, SendVerificationView,
                        GetPhoneNumberVerificationCodeSMSView,
                        GetPhoneNumberVerificationCodeCallView,
                        PhoneNumberVerificationView,
                        HelpDocumentationView,
                        PendoView,
                        TermsAndConditionAcceptanceView,
                        ZohoPermissionsView,
                        NewsletterSubscriptionViewSet,)
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
                               VendorClientCodeView,
                               EstimateSignView, EstimateSignCompleteView,
                               GetDocumentStatus, GetSignURL,
                               TemplateSignView, GetDistanceView,
                               GetSalesPersonView, GetTemplateStatus,
                               CustomerPaymentView, GetBoxTokenAuthenticationView,
                               BillView, SalesOrderView, EstimateAddressView,
                               ContactPersonView, CRMVendorTierView, GetNewsFeedView,
                               GetRecordView, LabTestView, GetAutoComplete,NotificationView,
                               DownloadSignDocumentView, CampaignView, MarkEstimateView,
                               ApproveEstimateView, MarkSalesOrderView, ApproveSalesOrderView,
                               SalesOrderSubStatusesView, MarkPurchaseOrderView, 
                               ApprovePurchaseOrderView, MarkInvoiceView, 
                               ApproveInvoiceView, MarkBillView, ApproveBillView,
                               ConvertEstimateToSalesOrder, ConvertSalesOrderToInvoice,ChatbotView,
                               ConvertEstimateToInvoice, ConvertSalesOrderToPurchaseOrder)

from fee_variable.views import (OrderVariableView,
                                CustomInventoryVariableView,
                                TaxVariableVariableView, )

from inventory.views import (InventoryViewSet, InventorySyncView,
                             CultivarCategoryView, InventoryStatusTypeView,
                             ItemFeedbackViewSet, InventoryUpdateDateView,
                             InTransitOrderViewSet, DocumentPreSignedView,
                             DocumentView, DocumentStatusView, InventoryDeleteView,
                             InventoryNutrientsView,InventoryCountyView,InventoryAppellationView,
                             InventoryEthicsView, CustomInventoryViewSet,InventoryClientCodeView,
                             InventoryWebHook,InventoryExportViewSet,InventoryCultivationTypeView,
                             InventoryItemEditViewSet, InventoryItemDelistViewSet,
                             SalesReturnView, PackageView, ContactView, InventoryMetaDataView,
                             ConvertSalesOrderToPackage,CultivarTypesView,InventoryTagsView, InTransitDeleteSyncView)
from cultivar.views import (CultivarViewSet, CultivarSyncView, )
from labtest.views import (LabTestViewSet, LabTestSyncViewSet, )
from permission.views import (PermissionListView,)
from brand.views import (
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
    OnboardingDataFetchViewSet,
    MyOrganizationRoleView,
)
from two_factor.views import (
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
# from brand.views import (InviteUserView,)
from bill.views import (EstimateWebappView, )

from compliance_binder.views import(
     BinderLicenseViewSet,
)

from internal_onboarding.views import (
     InternalOnboardingView,
)

from seo.views import (
     PageMetaView,
)

from core.admin_sites import logger_admin_site

router = SimpleRouter()
router.register(r'user/login', TwoFactoLogInViewSet, base_name="login-2fa")
router.register(r'user', UserViewSet, base_name="user")
router.register(r'inventory', InventoryViewSet, base_name="inventory")
router.register(r'custom-inventory', CustomInventoryViewSet, base_name="inventory")
router.register(r'inventory-edit', InventoryItemEditViewSet, base_name="inventory-change")
router.register(r'inventory-delist', InventoryItemDelistViewSet, base_name="inventory-delete")
router.register(r'item-feedback', ItemFeedbackViewSet, base_name="feedback")
router.register(r'cultivar', CultivarViewSet, base_name="cultivar")
router.register(r'labtest', LabTestViewSet, base_name="labtest")
router.register(r'organization', OrganizationViewSet, base_name="organization")
router.register(r'license', LicenseViewSet, 'license-all')
router.register(r'export-inventory', InventoryExportViewSet, base_name="inventory-export")

router.registry.extend([
    ('organization/(?P<parent_organization>[^/.]+)/brand', BrandViewSet, 'brand'),
    ('organization/(?P<parent_organization>[^/.]+)/license', LicenseViewSet, 'license'),
    ('organization/(?P<parent_organization>[^/.]+)/role', OrganizationRoleViewSet, 'organization-role'),
    ('organization/(?P<parent_organization>[^/.]+)/user', OrganizationUserViewSet, 'organization-user'),
    ('organization/(?P<parent_organization>[^/.]+)/user/(?P<parent_organization_user>[^/.]+)/role', OrganizationUserRoleViewSet, 'organization-user-role-nest'),
    ('organization/(?P<parent_organization>[^/.]+)/invite-user', InviteUserViewSet, 'organization-invite-user'),
])

router.register(r'compliance-binder/license', BinderLicenseViewSet, base_name="binder-license")
router.register(r'profile-report', ProfileReportViewSet, base_name="report")
router.register(r'in-transit-order', InTransitOrderViewSet, base_name="in_transit_order")
router.register(r'help-documentation', HelpDocumentationView, base_name="help-documentation")
router.register(r'onboarding-data-fetch', OnboardingDataFetchViewSet, base_name="onboarding-data-fetch")

router.register(r'two-factor/device', TwoFactorDeviceViewSet, base_name="two-factor-device")
router.register(r'two-factor/add-device/authy-one-touch', AuthyAddUserRequestViewSet, base_name="add-authy-user")
router.register(r'two-factor/add-device/phone', AddPhoneDeviceViewSet, base_name="add-phone-device")
router.register(r'two-factor/add-device/authenticator', AddAuthenticatorRequestViewSet, base_name="add-authenticator-device")
router.register(r'order-variables', OrderVariableView, base_name="order-variables")
router.register(r'inventory-variables', CustomInventoryVariableView, base_name="inventory-variables")
router.register(r'tax-variables', TaxVariableVariableView, base_name="tax-variables")
router.register(r'internal-onboarding', InternalOnboardingView, base_name="internal-onboarding")
router.register(r'newsletter-subscription', NewsletterSubscriptionViewSet, base_name="newsletter-subscription")



urlpatterns = [
    path('admin/', admin.site.urls),
    path('logger/', logger_admin_site.urls),
    path(r'user/me/', MeView.as_view(), name='user-me'),
    # path(r'user/login/', LogInView.as_view(), name='login'),
    path(r'user/logout/', LogoutAllView.as_view(), name='logout'), #LogoutView - removes only single related token from DB.
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
    path(r'search/licenses/', SearchLicenseView.as_view(), name='search-licenses'),
    path(r'box/link/', GetBoxSharedLink.as_view(), name='get_shared_link'),
    path(r'integration/box/', GetBoxTokensView.as_view(), name='box'),
    path(r'notify/', NotificationView.as_view(), name='notification'),
    path(r'integration/box-aws/',
         GetBoxTokenAuthenticationView.as_view(), name='box-token-authentication'),
    path(r'crm/search/cultivar', SearchCultivars.as_view(), name='search_cultivar'),
    path(r'crm/picklist/', GetPickListView.as_view(), name='get_picklist'),
    path(r'crm/account-picklist/', GetPickListAccountView.as_view(),
         name='get_account_picklist'),
    path(r'crm/contact/', CRMContactView.as_view(), name='list_crm_contacts'),
    path(r'crm/', GetRecordView.as_view(), name='get_crm_record'),
    path(r'crm/lead/', LeadView.as_view(), name='create_lead'),
    path(r'crm/lead-sources/', LeadSourcesView.as_view(), name='get_lead_sources'),
    path(r'crm/vendor/', CRMVendorView.as_view(), name='get_vendor'),
    path(r'crm/vendor-tier/', CRMVendorTierView.as_view(), name='update_tier'),
    path(r'crm/account-client-code/', ClientCodeView.as_view(),
         name='get_account_client_code'),
    path(r'crm/vendor-client-code/', VendorClientCodeView.as_view(),name='get_vendor_client_code'),
    path(r'cultivar/sync/', CultivarSyncView.as_view(), name='sync_cultivar'),
    path(r'books/estimate/sales-rep/', EstimateWebappView.as_view(), name="estimate-sales-rep-view"),
    path(r'books/estimate/sales-rep/<str:id>/', EstimateWebappView.as_view(), name="estimate-sales-rep-view"),
    path(r'books/estimate/', EstimateView.as_view(), name='estimate'),
    path(r'books/estimate-address/', EstimateAddressView.as_view(), name='estimate_address'),
    path(r'books/contact/', ContactView.as_view(), name='contact'),
    path(r'books/contact-person/', ContactPersonView.as_view(), name='contact-person'),
    path(r'books/contact-address/',
         ContactAddressView.as_view(), name='contact_address'),
    path(r'books/purchase-order/',
         PurchaseOrderView.as_view(), name='purchase_order'),
    path(r'books/vendor-payment/',
         VendorPaymentView.as_view(), name='vendor_payment'),
    path(r'books/customer-payment/',
         CustomerPaymentView.as_view(), name='customer_payment'),
    path(r'books/invoice/', InvoiceView.as_view(), name='invoices'),
    path(r'books/bill/', BillView.as_view(), name='bills'),
    path(r'books/sales-order/', SalesOrderView.as_view(), name='sales-orders'),
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
    path(r'cultivar-type/', CultivarTypesView.as_view(),
         name='cultivar_types'),
    path(r'inventory/client-code', InventoryClientCodeView.as_view(),
         name='inventory_client_code'),
    path(r'inventory/cultivation-type', InventoryCultivationTypeView.as_view(),
         name='inventory_cultivation_type'),
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
    #path(r'order-variables/', OrderVariableView.as_view(), name='order-variables'),
    path(r'crm/sales-person/', GetSalesPersonView.as_view(),
         name='get_sales_person'),
    path(r'profile-category/', ProfileCategoryView.as_view(), name='category'),
    path(r'platform-kpi/', KpiViewSet.as_view(), name='kpi'),
    path('organization/<int:parent_organization>/platform-kpi/', KpiViewSet.as_view(), name='organization-kpi'),
    path('organization/<int:parent_organization>/my-permissions/', MyOrganizationRoleView.as_view(), name='my-permissions'),
    path(r'file-upload/', FileUploadView.as_view(), name='file-upload'),
    path(r'document-url/<str:id>/', DocumentPreSignedView.as_view(), name='documents-url'),
    path(r'document-url/', DocumentPreSignedView.as_view(), name='documents-url'),
    path(r'document-status/<str:id>/', DocumentStatusView.as_view(), name='extra-documents'),
    path(r'document/', DocumentView.as_view(), name='extra-documents'),
    path(r'document/<str:id>/', DocumentView.as_view(), name='extra-documents'),
    path(r'terms-and-condition-acceptance/', TermsAndConditionAcceptanceView.as_view(), name='terms-and-condition-acceptance'),
    path(r'license/sync/', LicenseSyncView.as_view(), name='license-sync'),
    path(r'news/', GetNewsFeedView.as_view(), name='news-feed'),
    path(r'crm/labtest/<str:labtest_id>/', LabTestView.as_view(), name='labtest'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    path(r'inventory/county/', InventoryCountyView.as_view(), name='get-county'),
    path(r'inventory/appellation/', InventoryAppellationView.as_view(), name='get-appellation'),
    path(r'inventory/nutrients/', InventoryNutrientsView.as_view(), name='get-nutrients'),#
    path(r'inventory/tags/', InventoryTagsView.as_view(), name='get-tags'),
    path(r'inventory/ethics-and-certification/', InventoryEthicsView.as_view(), name='get-ethics_and_certification'),
    path(r'permission-list/', PermissionListView.as_view(), name="permission-list"),
    path(r'user-invitation-verify/', UserInvitationVerificationView.as_view(), name="user-invitation-verify"),
    path(r'update-program-selection/', ProgramSelectionSyncView.as_view(), name="update-program"),
    path(r'autocomplete/', GetAutoComplete.as_view(), name="address-autocomplete"),
    path(r'sign/download/', DownloadSignDocumentView.as_view(), name="download-sign-document"),
    path(r'inventory/update/', InventoryWebHook.as_view(), name="inventory-webhook"),
    path(r'campaign/', CampaignView.as_view(), name="campaign"),
    path(r'inventory/package/', PackageView.as_view(), name="inventory-packages"),
    path(r'inventory/sales-return/', SalesReturnView.as_view(), name="inventory-sales-returns"),
    path(r'inventory/contact/', ContactView.as_view(), name="inventory-contact"),
    path(r'books/estimate/status/', MarkEstimateView.as_view(), name="mark-estimate"),
    path(r'books/estimate/approve/', ApproveEstimateView.as_view(), name="approve-estimate"),
    path(r'books/sales-order/status/', MarkSalesOrderView.as_view(), name="mark-salesorder"),
    path(r'books/sales-order/approve/', ApproveSalesOrderView.as_view(), name="approve-salesorder"),
    path(r'books/purchase-order/status/', MarkPurchaseOrderView.as_view(), name="mark-purchaseorder"),
    path(r'books/purchase-order/approve/', ApprovePurchaseOrderView.as_view(), name="approve-purchaseorder"),
    path(r'books/invoice/status/', MarkInvoiceView.as_view(), name="mark-invoice"),
    path(r'books/invoice/approve/', ApproveInvoiceView.as_view(), name="approve-invoice"),
    path(r'books/bill/status/', MarkBillView.as_view(), name="mark-bill"),
    path(r'books/bill/approve/', ApproveBillView.as_view(), name="approve-bill"),
    path(r'books/sales-order/sub-statuses/', SalesOrderSubStatusesView.as_view(), name="sales-order-sub-statuses"),
    path(r'inventory/metadata/', InventoryMetaDataView.as_view(), name="inventory-metadata"),
    path(r'pendo/me/', PendoView.as_view(), name='pendo-me'),
    path(r'books/estimate/convert/sales-order/', ConvertEstimateToSalesOrder.as_view(), name="convert-estimate-to-salesorder"),
    path(r'books/sales-order/convert/invoice/', ConvertSalesOrderToInvoice.as_view(), name="convert-so-to-invoice"),
    path(r'books/estimate/convert/invoice/', ConvertEstimateToInvoice.as_view(), name="convert-estimate-to-invoice"),
    path(r'books/sales-order/convert/purchase-order/', ConvertSalesOrderToPurchaseOrder.as_view(), name="convert-so-to-po"),
    path(r'inventory/sales-order/convert/package/', ConvertSalesOrderToPackage.as_view(), name="convert-so-to-package"),
    path(r'intransit/sync/', InTransitDeleteSyncView.as_view(), name="intransit-delete-sync"),
    path(r'books/permission/', ZohoPermissionsView.as_view(), name="zoho-permission"),
    path(r'seo/page-meta/', PageMetaView.as_view(), name="page-meta"),
    path(r'bot/', ChatbotView.as_view(), name="chat-bot"),
] + router.urls


if not settings.DEBUG:
    urlpatterns += [
        url(r'^static\/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT})
        
    ]
