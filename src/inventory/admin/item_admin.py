from django.contrib import admin
from django.conf import settings
from django.contrib.admin.filters import (
    BooleanFieldListFilter,
)
from core.mixins.admin_filters import (
    NullListFilter,
)

from ..models import (
    Inventory,
)
from ..tasks.qr_code import generate_upload_item_detail_qr_code_stream
from integration.box import (search,delete_file)
from django.http import HttpResponseRedirect
from fee_variable.models import QRCodeVariable

class InventoryItemAdmin(admin.ModelAdmin):
    """
    Admin
    """

    model = Inventory
    list_display = (
        "name",
        "sku",
        "category_name",
        "cf_vendor_name",
        "actual_available_stock",
        "price",
        "pre_tax_price",
        "cf_farm_price_2",
        "cf_trim_qty_lbs",
        "cf_raw_material_input_g",
        "cf_batch_qty_g",
        "cf_status",
        "cf_cfi_published",
        "inventory_name",
        "created_time",
    )
    list_filter = (
        "category_name",
        "status",
        "cf_status",
        "cf_cfi_published",
        "inventory_name",
        ("pre_tax_price", NullListFilter),
    )
    search_fields = (
        "sku",
        "name",
    )
    ordering = ("-created_time",)

    fieldsets = (
        (None, {
            'fields': (
                'item_id',
                'item_type',
                'product_type',
                'status',
                'inventory_name',
                'is_combined_product',
            ),
        }),
        ('Related', {
            'fields': (
                'cultivar',
                'labtest',
                'cf_lab_test_sample_id',
            ),
        }),
        ('item info', {
            'fields': (
                'name',
                'sku',
                'cf_cfi_published',
                'cf_status',
                'unit',
                'category_id',
                'category_name',
                'parent_category_name',
                'vendor_id',
                'vendor_name',
                'cf_vendor_name',
                'cf_strain_name',
                'cf_cultivation_type',
                'cf_cannabis_grade_and_category',
                'cf_client_code',
                'cf_pending_sale',
                'cf_cultivar_type',
                'cf_procurement_rep',
                'cf_batch_notes',
                'cf_sample_in_house',
                'cf_available_date',
                'cf_date_available',
                'tags',
            ),
        }),
        ('Pricing', {
            'fields': (
                'cf_biomass',
                'cf_trim_qty_lbs',
                'cf_raw_material_input_g',
                'cf_batch_qty_g',
                'purchase_rate',
                # 'cf_farm_price',
                'cf_farm_price_2',
                'cf_mscp',
                'pre_tax_price',
                'cf_cultivation_tax',
                'price',
                'cf_seller_position',
                'cf_payment_method',
                'cf_payment_terms',
                'is_taxable',
                'tax_id',
                'tax_name',
                'tax_type',
                'tax_exemption_code',
                'tax_percentage',
            ),
        }),
        ('Profile Info', {
            'fields': (
                'county_grown',
                'appellation',
            ),
        }),
        ('Stock', {
            'fields': (
                'actual_available_for_sale_stock',
                'available_for_sale_stock',
                'actual_available_stock',
                'available_stock',
                'total_initial_stock',
                'stock_on_hand',
            ),
        }),
        ('Accounts', {
            'fields': (
                'account_id',
                'account_name',
                'purchase_account_id',
                'purchase_account_name',
                'inventory_account_id',
                'inventory_account_name',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'last_modified_time',
                'created_time',
                'image_name',
                'image_type',
                'manufacturer',
                'brand',
                'zcrm_product_id',
                'description',
                'is_returnable',
                'cf_lab_file',
                'cf_ifp_farm',
                'cf_procurement_confirmed',
                'cf_marge_per_unit',
                'cf_lpn',
                'cf_pending_sale_1_1',
                'cf_pending_sale_2',
                'cf_pending_sale_3',
                'cf_metrc_manifest_number',
                'cf_harvest',
                'cf_received_date',
                'cf_metrc_packages',
                'cf_lab_test_link',
                'cf_testing_type',
                'cf_pesticide_summary',
                'cf_next_harvest_date',
                'cf_manufacturing_date',
                'cf_batch_blending',
                'cf_lab_testing_status',
                'cf_qa_intake_grading_sheet_id',
                'cf_administrative_hold',
                'cf_lab_test_results_box_url',
                'track_batch_number',
                'cf_quantity_estimate',
                'cf_metrc_source_package_id',
                'cf_market_feedback',
                'cf_minimum_quantity',
                'package_details',
                'documents',
                'batches',
                'current_price_change',
                'thumbnail_url',
                'mobile_url',
                'nutrients',
                'ethics_and_certification',
                'mapped_items',
                'client_id',
                'item_qr_code_url',
                'qr_code_box_id',
                'qr_box_direct_url',
                # 'extra_documents',
            ),
        }),
    )
    change_form_template = 'user/qr_code.html'

    def response_change(self, request, obj):
        if "_trigger-qr" in request.POST:
            size_obj = QRCodeVariable.objects.values('qr_code_size')[0]
            box_obj_id = search(settings.INVENTORY_QR_UPLOAD_FOLDER_ID,"%s.png"%obj.item_id)
            if box_obj_id:
                delete_file(box_obj_id)
            generate_upload_item_detail_qr_code_stream(obj.item_id,size_obj['qr_code_size'])
            self.message_user(request, "Task Triggered.Check refreshed URL mapped to field 'QR Code-Box URL'!")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
