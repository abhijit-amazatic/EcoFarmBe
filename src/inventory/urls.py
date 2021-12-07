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
    InventoryViewSet,
    InventorySyncView,
    CultivarCategoryView,
    InventoryStatusTypeView,
    ItemFeedbackViewSet,
    InventoryUpdateDateView,
    InTransitOrderViewSet,
    DocumentPreSignedView,
    DocumentView,
    DocumentStatusView,
    InventoryDeleteView,
    InventoryNutrientsView,
    InventoryCountyView,
    InventoryAppellationView,
    InventoryEthicsView,
    CustomInventoryViewSet,
    InventoryClientCodeView,
    InventoryWebHook,
    InventoryExportViewSet,
    InventoryCultivationTypeView,
    InventoryItemEditViewSet,
    InventoryItemDelistViewSet,
    SalesReturnView,
    PackageView,
    ContactView,
    InventoryMetaDataView,
    ConvertSalesOrderToPackage,
    CultivarTypesView,
    InventoryTagsView,
    InTransitDeleteSyncView,
    InventoryUpdateView,
    CategoryNameView,
    PendingOrderAdminView,
    InventoryLicenseClientIdView,
)

app_name = "inventory"

router = SimpleRouter()
router.register(r'inventory', InventoryViewSet, base_name="inventory")
router.register(r'custom-inventory', CustomInventoryViewSet, base_name="custom-inventory")
router.register(r'inventory-edit', InventoryItemEditViewSet, base_name="inventory-edit")
router.register(r'inventory-delist', InventoryItemDelistViewSet, base_name="inventory-delist")
router.register(r'item-feedback', ItemFeedbackViewSet, base_name="feedback")
router.register(r'export-inventory', InventoryExportViewSet, base_name="inventory-export")
router.register(r'in-transit-order', InTransitOrderViewSet, base_name="in_transit_order")

urlpatterns = [
    path(r'document-url/<str:id>/', DocumentPreSignedView.as_view(), name='documents-url'),
    path(r'document-url/', DocumentPreSignedView.as_view(), name='documents-url'),
    path(r'document-status/<str:id>/', DocumentStatusView.as_view(), name='extra-documents'),
    path(r'document/', DocumentView.as_view(), name='extra-documents'),
    path(r'document/<str:id>/', DocumentView.as_view(), name='extra-documents'),

    path(r'inventory/pending-order/', PendingOrderAdminView.as_view(), name="pending-order-admin-view"),
    path(r'inventory/sync', InventorySyncView.as_view(), name='sync_inventory'),
    path(r'inventory/cultivar', CultivarCategoryView.as_view(), name='cultivar-category'),
    path(r'inventory/category-name', CategoryNameView.as_view(), name='category-name'),
    path(r'cultivar-type/', CultivarTypesView.as_view(), name='cultivar_types'),
    path(r'inventory/client-code', InventoryClientCodeView.as_view(), name='client-code'),
    path(r'inventory/license/client-id', InventoryLicenseClientIdView.as_view(), name='license-client-code'),
    path(r'inventory/cultivation-type', InventoryCultivationTypeView.as_view(), name='cultivation-type'),
    path(r'inventory/status/', InventoryStatusTypeView.as_view(), name='status-types'),
    path(r'inventory/last-modified-time/', InventoryUpdateDateView.as_view(), name='last-modified-time'),
    path(r'delete-item/<str:item_id>/', InventoryDeleteView.as_view(), name='delete_inventory'),
    path(r'inventory/county/', InventoryCountyView.as_view(), name='get-county'),
    path(r'inventory/appellation/', InventoryAppellationView.as_view(), name='get-appellation'),
    path(r'inventory/nutrients/', InventoryNutrientsView.as_view(), name='get-nutrients'),#
    path(r'inventory/tags/', InventoryTagsView.as_view(), name='get-tags'),
    path(r'inventory/ethics-and-certification/', InventoryEthicsView.as_view(), name='ethics-and-certification'),
    path(r'inventory/update/', InventoryWebHook.as_view(), name="inventory-webhook"),
    path(r'inventory-update/', InventoryUpdateView.as_view(), name="inventory-update"),
    path(r'inventory/package/', PackageView.as_view(), name="inventory-packages"),
    path(r'inventory/sales-return/', SalesReturnView.as_view(), name="inventory-sales-returns"),
    path(r'inventory/contact/', ContactView.as_view(), name="inventory-contact"),
    path(r'inventory/metadata/', InventoryMetaDataView.as_view(), name="inventory-metadata"),
    path(r'inventory/sales-order/convert/package/', ConvertSalesOrderToPackage.as_view(), name="convert-so-to-package"),
    path(r'intransit/sync/', InTransitDeleteSyncView.as_view(), name="intransit-delete-sync"),
] + router.urls
