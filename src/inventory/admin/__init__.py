from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.db import models
from django.shortcuts import (reverse, )

from django_json_widget.widgets import JSONEditorWidget
from import_export import resources
from import_export.admin import (ImportExportModelAdmin, ExportActionMixin)

from core import settings
from core.settings import (AWS_BUCKET, )
from brand.models import LicenseProfile
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
from .inventory_item_delist import (
    InventoryItemDelistAdmin,
)
from .item_admin import (
    InventoryItemAdmin,
)


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
    


admin.site.register(Inventory, InventoryItemAdmin)
admin.site.register(InventoryItemEdit, InventoryItemEditAdmin)
admin.site.register(InventoryItemDelist, InventoryItemDelistAdmin)
# admin.site.register(InventoryItemQuantityAddition, InventoryItemQuantityAdditionAdmin)
admin.site.register(County, CountyAdmin)
#admin.site.register(Vendor, VendorAdmin)
admin.site.register(DailyInventoryAggrigatedSummary, DailyInventoryAggrigatedSummaryAdmin)
admin.site.register(InTransitOrder, InTransitOrderAdmin)
admin.site.register(CustomInventory, CustomInventoryAdmin)


