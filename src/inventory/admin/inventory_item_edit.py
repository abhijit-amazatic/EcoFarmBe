from django.contrib import admin

from core.mixins.admin import (CustomButtonMixin,)
from ..tasks.helpers import (
    inventory_item_change,
    add_item_quantity,
)




class InventoryItemEditAdmin(CustomButtonMixin, admin.ModelAdmin):
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
        'status',
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
                'marketplace_status',
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

    custom_buttons=('approve',)
    # custom_buttons_prop = {
    #     'approve': {
    #         'label': 'Approve',
    #         'color': '#ba2121',
    #     }
    # }

    def show_approve_button(self, request, obj,  add=False, change=False):
        return change and obj and obj.status == 'pending_for_approval'

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            inventory_item_change(obj, request)

    def cultivar_name(self, obj):
        return obj.item.cultivar.cultivar_name


class InventoryItemQuantityAdditionAdmin(CustomButtonMixin, admin.ModelAdmin):
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

    custom_buttons=('approve',)
    # custom_buttons_prop = {
    #     'approve': {
    #         'label': 'Approve',
    #         'color': '#ba2121',
    #     }
    # }

    def show_approve_button(self, request, obj,  add=False, change=False):
        return change and obj and obj.status == 'pending_for_approval'

    def approve(self, request, obj):
        add_item_quantity(obj, request)

    def cultivar_name(self, obj):
        return obj.item.cultivar.cultivar_name
