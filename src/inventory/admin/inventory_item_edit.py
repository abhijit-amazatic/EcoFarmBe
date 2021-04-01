from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils import timezone

from core import settings

from .mixin import AdminApproveMixin
from ..task_helpers import inventory_item_change




class InventoryItemsChangeRequestAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'item',
        'quantity_available',
        'farm_price',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        # 'status',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    fieldsets = (
        (None, {
            'fields': (
                'item',
                'farm_price',
                'quantity_available',
                'pricing_position',
                'have_minimum_order_quantity',
                'minimum_order_quantity',
                'payment_terms',
                'payment_method',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'approved_by',
                'approved_on',
                'created_by',
                'created_on',
                'updated_on',
            ),
        }),
    )
    # inlines = [InlineDocumentsAdmin,]
    # actions = ['test_action', ]


    def approve(self, request, obj):
        inventory_item_change(obj, request)

    def cultivar_name(self, obj):
            return obj.item.cultivar.cultivar_name
