from django.contrib import admin

from core.mixins.admin import (CustomButtonMixin,)

from ..tasks.inventory_item_quantity_addition import (
    add_item_quantity,
)


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

    custom_buttons=('approve',)
    # custom_buttons_prop = {
    #     'approve': {
    #         'label': 'Approve',
    #         'color': '#ba2121',
    #     }
    # }

    def show_approve_button(self, request, obj,  add=False, change=False):
        return change and obj and obj.status == 'pending_for_approval'

    def cultivar_name(self, obj):
        return obj.item.cultivar.cultivar_name


    def approve(self, request, obj):
        add_item_quantity(obj, request)

