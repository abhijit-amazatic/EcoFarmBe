from django.contrib import admin

from .mixin import AdminApproveMixin
from ..tasks.helpers import (
    inventory_item_change,
    add_item_quantity,
)
from ..tasks import (
    notify_inventory_item_change_approved_task,
)




class InventoryItemEditAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'item',
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
                'pricing_position',
                'have_minimum_order_quantity',
                'minimum_order_quantity',
                'batch_availability_date',
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
        if obj.status == 'pending_for_approval':
            inventory_item_change(obj, request)
            if obj.status == 'approved':
                notify_inventory_item_change_approved_task(obj.id)


    def cultivar_name(self, obj):
        return obj.item.cultivar.cultivar_name


class InventoryItemQuantityAdditionAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'item',
        'quantity',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        # 'status',
        'po_id',
        'po_number',
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
                'quantity',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'po_id',
                'po_number',
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
        add_item_quantity(obj, request)

    def cultivar_name(self, obj):
        return obj.item.cultivar.cultivar_name
