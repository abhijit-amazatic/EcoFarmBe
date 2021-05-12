from django.contrib import admin
from django.db import models
from django.shortcuts import (reverse, )

from import_export import resources


from core import settings
from core.settings import (AWS_BUCKET, )
from import_export.admin import (ImportExportModelAdmin, ExportActionMixin)

from ..models import (
    Inventory,
    CustomInventory,
    Documents,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
    InventoryItemEdit,
    InventoryItemQuantityAddition,
)
from .custom_inventory import CustomInventoryAdmin
from .inventory_item_edit import (
    InventoryItemEditAdmin,
    InventoryItemQuantityAdditionAdmin,
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


class DailyInventoryAggrigatedSummaryAdmin(ExportActionMixin,admin.ModelAdmin):
    """
    Summary Admin.
    """
    model = DailyInventoryAggrigatedSummary
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


class InventoryAdmin(admin.ModelAdmin):
    """
    Admin
    """
    model = Inventory
    list_display = (
        'name',
        'cf_vendor_name',
        'sku',
        'actual_available_stock',
        'price',
        'cf_farm_price_2',
        'created_time'
    )
    search_fields = ('sku', 'name',)
    ordering = ('-created_time',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False




admin.site.register(Inventory, InventoryAdmin)
admin.site.register(InventoryItemEdit, InventoryItemEditAdmin)
admin.site.register(InventoryItemQuantityAddition, InventoryItemQuantityAdditionAdmin)
admin.site.register(County, CountyAdmin)
admin.site.register(DailyInventoryAggrigatedSummary, DailyInventoryAggrigatedSummaryAdmin)
admin.site.register(CustomInventory, CustomInventoryAdmin)


