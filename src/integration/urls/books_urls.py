"""
URL Configuration
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from ..views import (
    EstimateView,
    ContactView as ContactViewBooks,
    PurchaseOrderView,
    VendorPaymentView,
    InvoiceView,
    AccountSummaryView,
    VendorCreditView,
    EstimateTaxView,
    GetTaxView,
    ContactAddressView,
    EstimateStatusView,
    EstimateSignView,
    EstimateSignCompleteView,
    GetDocumentStatus,
    GetSignURL,
    CustomerPaymentView,
    BillView,
    SalesOrderView,
    EstimateAddressView,
    ContactPersonView,
    MarkEstimateView,
    ApproveEstimateView,
    MarkSalesOrderView,
    ApproveSalesOrderView,
    SalesOrderSubStatusesView,
    MarkPurchaseOrderView,
    ApprovePurchaseOrderView,
    MarkInvoiceView,
    ApproveInvoiceView,
    MarkBillView,
    ApproveBillView,
    ConvertEstimateToSalesOrder,
    ConvertSalesOrderToInvoice,
    ConvertEstimateToInvoice,
    ConvertSalesOrderToPurchaseOrder,
)

app_name = "integration"

router = SimpleRouter()

urlpatterns = [
    path(r'estimate/', EstimateView.as_view(), name='estimate'),
    path(r'estimate-address/', EstimateAddressView.as_view(), name='estimate_address'),
    path(r'contact/', ContactViewBooks.as_view(), name='books-contact'),
    path(r'contact-person/', ContactPersonView.as_view(), name='contact-person'),
    path(r'contact-address/', ContactAddressView.as_view(), name='contact_address'),
    path(r'purchase-order/', PurchaseOrderView.as_view(), name='purchase_order'),
    path(r'vendor-payment/', VendorPaymentView.as_view(), name='vendor_payment'),
    path(r'customer-payment/', CustomerPaymentView.as_view(), name='customer_payment'),
    path(r'invoice/', InvoiceView.as_view(), name='invoices'),
    path(r'bill/', BillView.as_view(), name='bills'),
    path(r'sales-order/', SalesOrderView.as_view(), name='sales-orders'),
    path(r'vendor-credits/', VendorCreditView.as_view(), name='vendor_credits'),
    path(r'account-summary/', AccountSummaryView.as_view(), name='account_summary'),
    path(r'calculate-tax/', EstimateTaxView.as_view(), name='calculate-tax'),
    path(r'tax/', GetTaxView.as_view(), name='get-tax'),
    path(r'estimate-status/', EstimateStatusView.as_view(), name='update_status'),
    path(r'sign-estimate/', EstimateSignView.as_view(), name='sign-estimate'),
    path(r'signed-estimate/', EstimateSignCompleteView.as_view(), name='sined-estimate'),
    path(r'sign-status/', GetDocumentStatus.as_view(), name='get-sign-status'),
    path(r'sign-url/', GetSignURL.as_view(), name='get-sign-url'),
    path(r'estimate/status/', MarkEstimateView.as_view(), name="mark-estimate"),
    path(r'estimate/approve/', ApproveEstimateView.as_view(), name="approve-estimate"),
    path(r'sales-order/status/', MarkSalesOrderView.as_view(), name="mark-salesorder"),
    path(r'sales-order/approve/', ApproveSalesOrderView.as_view(), name="approve-salesorder"),
    path(r'purchase-order/status/', MarkPurchaseOrderView.as_view(), name="mark-purchaseorder"),
    path(r'purchase-order/approve/', ApprovePurchaseOrderView.as_view(), name="approve-purchaseorder"),
    path(r'invoice/status/', MarkInvoiceView.as_view(), name="mark-invoice"),
    path(r'invoice/approve/', ApproveInvoiceView.as_view(), name="approve-invoice"),
    path(r'bill/status/', MarkBillView.as_view(), name="mark-bill"),
    path(r'bill/approve/', ApproveBillView.as_view(), name="approve-bill"),
    path(r'sales-order/sub-statuses/', SalesOrderSubStatusesView.as_view(), name="sales-order-sub-statuses"),
    path(r'estimate/convert/sales-order/', ConvertEstimateToSalesOrder.as_view(), name="convert-estimate-to-salesorder"),
    path(r'sales-order/convert/invoice/', ConvertSalesOrderToInvoice.as_view(), name="convert-so-to-invoice"),
    path(r'estimate/convert/invoice/', ConvertEstimateToInvoice.as_view(), name="convert-estimate-to-invoice"),
    path(r'sales-order/convert/purchase-order/', ConvertSalesOrderToPurchaseOrder.as_view(), name="convert-so-to-po"),
] + router.urls
