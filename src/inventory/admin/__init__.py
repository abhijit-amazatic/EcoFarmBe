from django.contrib import admin
from django.db import models
from django.shortcuts import (reverse, )
from django.contrib.contenttypes.admin import GenericStackedInline
from import_export import resources
from core import settings
from core.settings import (AWS_BUCKET, )
from import_export.admin import (ImportExportModelAdmin, ExportActionMixin)
from brand.models import LicenseProfile
from django import forms
from ..models import (
    Inventory,
    CustomInventory,
    Documents,
    DailyInventoryAggrigatedSummary,
    SummaryByProductCategory,
    County,
    CountyDailySummary,
    InTransitOrder,
    InventoryItemEdit,
    InventoryItemQuantityAddition,
    InventoryItemDelist,
    Vendor,
    VendorDailySummary,
    Summary,
)
from .custom_inventory import CustomInventoryAdmin
from .inventory_item_edit import (
    InventoryItemEditAdmin,
)
from .inventory_item_quantity_addition import (
    InventoryItemQuantityAdditionAdmin,
)
from .inventory_item_delist import (InventoryItemDelistAdmin, )
from django_json_widget.widgets import JSONEditorWidget



class DailyInventoryAggrigatedSummaryResource(resources.ModelResource):

    class Meta:
        model = DailyInventoryAggrigatedSummary
        fields = (
            'date',
            'total_thc_max',
            'total_thc_min',
            'batch_varities',
            'average',
            'total_value',
            'smalls_quantity',
            'tops_quantity',
            'total_quantity',
            'trim_quantity',
            'average_thc',
        )
        #exclude = ('imported', )
        #export_order = ('id', 'price', 'author', 'name')


class InlineSummaryByProductCategoryAdmin(admin.TabularInline):
    extra = 0
    model = SummaryByProductCategory
    readonly_fields = (
        'product_category',
        'total_thc_max',
        'total_thc_min',
        'batch_varities',
        'average',
        'total_value',
        'smalls_quantity',
        'tops_quantity',
        'total_quantity',
        'trim_quantity',
        'average_thc',
    )
    can_delete = False

    
class DailyInventoryAggrigatedSummaryAdmin(ExportActionMixin,admin.ModelAdmin):
    """
    Summary Admin.
    """
    model = DailyInventoryAggrigatedSummary
    inlines = (InlineSummaryByProductCategoryAdmin,)
    search_fields = ('date',)
    list_display = ('date',)
    ordering = ('-date',)
    readonly_fields = (
        'date',
        'total_thc_max',
        'total_thc_min',
        'batch_varities',
        'average',
        'total_value',
        'smalls_quantity',
        'tops_quantity',
        'total_quantity',
        'trim_quantity',
        'average_thc',
    )
    resource_class = DailyInventoryAggrigatedSummaryResource


class InlineCountyDailySummaryAdminResource(resources.ModelResource):

    class Meta:
        model = CountyDailySummary
        fields = (
            'date',
            'county__name',
            'total_thc_max',
            'total_thc_min',
            'batch_varities',
            'average',
            'total_value',
            'smalls_quantity',
            'tops_quantity',
            'total_quantity',
            'trim_quantity',
            'average_thc',
        )


class InlineCountyDailySummaryAdmin(admin.TabularInline):
    extra = 0
    model = CountyDailySummary
    list_display = ('date', 'county__name',)
    readonly_fields = (
        'date',
        'county',
        'total_thc_max',
        'total_thc_min',
        'batch_varities',
        'average',
        'total_value',
        'smalls_quantity',
        'tops_quantity',
        'total_quantity',
        'trim_quantity',
        'average_thc',
    )
    search_fields = ('date', 'county__name',)
    can_delete = False



class CountyAdmin(ExportActionMixin, admin.ModelAdmin):
    """
    Admin
    """
    inlines = (InlineCountyDailySummaryAdmin,)
    model = County
    search_fields = ('name',)
    ordering = ('-name',)
    readonly_fields = ('name',)
    resource_class = InlineCountyDailySummaryAdminResource

    def get_export_data(self, file_format, queryset, *args, **kwargs):
        """
        Returns file_format representation for given queryset.
        """
        res_qs = CountyDailySummary.objects.filter(county__in=queryset).order_by('-county__name')
        return super().get_export_data(file_format, res_qs, *args, **kwargs)


class InlineVendorDailySummaryAdmin(GenericStackedInline):
    extra = 0
    model = Summary
    ct_field = "content_type"
    ct_fk_field = "object_id"
    can_delete = False
    
class VendorAdmin(ExportActionMixin, admin.ModelAdmin):
    """
    Admin
    """
    inlines = (InlineVendorDailySummaryAdmin,)
    model = Vendor
    list_display  = ('cf_client_code','vendor_name')
    search_fields = ('vendor_name','cf_client_code')
   
    
class InventoryAdmin(admin.ModelAdmin):
    """
    Admin
    """
    model = Inventory
    list_display = (
        'name',
        'sku',
        'category_name',
        'cf_vendor_name',
        'actual_available_stock',
        'price',
        'pre_tax_price',
        'cf_farm_price_2',
        'cf_trim_qty_lbs',
        'cf_batch_qty_g',
        'cf_status',
        'cf_cfi_published',
        'inventory_name',
        'created_time'
    )
    list_filter = ('category_name', 'status', 'cf_status', 'cf_cfi_published', 'inventory_name')
    search_fields = ('sku', 'name',)
    ordering = ('-created_time',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class InTransitForm(forms.ModelForm):
    class Meta:
        model = InTransitOrder
        fields = '__all__'
        widgets = {
            'order_data': JSONEditorWidget(options={'mode':'tree','search': True}),
        }
        
class InTransitOrderAdmin(admin.ModelAdmin):
    """
    Admin for itransit/pending urder.
    """
    model = InTransitOrder
    search_fields = ('user__email',)
    list_display = ('user','profile_id','total_cart_item','profile','created_on',)
    ordering = ('-created_on',)
    readonly_fields = ('profile_id',)
    form = InTransitForm

    def total_cart_item(self, obj):
        if obj.order_data:
            obj_list  = obj.order_data.get('cart_item',[])
            return len(obj_list)
        return 0
    total_cart_item.short_description = 'Total Items'
    
    def profile(self, obj):
        return LicenseProfile.objects.get(id=obj.profile_id)
    


admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItemEdit, InventoryItemEditAdmin)
admin.site.register(InventoryItemDelist, InventoryItemDelistAdmin)
# admin.site.register(InventoryItemQuantityAddition, InventoryItemQuantityAdditionAdmin)
admin.site.register(County, CountyAdmin)
#admin.site.register(Vendor, VendorAdmin)
admin.site.register(DailyInventoryAggrigatedSummary, DailyInventoryAggrigatedSummaryAdmin)
admin.site.register(InTransitOrder, InTransitOrderAdmin)
admin.site.register(CustomInventory, CustomInventoryAdmin)


