from django.utils import timezone
from django.contrib import admin
from django.contrib import messages

from core.mixins.admin import (CustomButtonMixin,)
from fee_variable.utils import (get_item_mcsp_fee,)
from utils import (get_approved_by, )

from integration.inventory import (
    update_inventory_item,
)
from ..tasks import (
    notify_inventory_item_change_approved_task,
)
from ..utils import (get_item_tax,)
from ..data import (CG,)



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

    custom_buttons = ('approve',)
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
            mcsp_fee = get_item_mcsp_fee(
                obj.vendor_name,
                license_profile=obj.license_profile,
                item_category_group=CG.get(obj.category_name),
                request=request,
            )
            if mcsp_fee:
                tax = get_item_tax(obj, request)
                if tax:
                    data = obj.get_item_update_data()
                    if obj.farm_price:
                        data['price'] = obj.farm_price + mcsp_fee + tax
                        data['rate'] = obj.farm_price + mcsp_fee + tax
                    inventory_org = data.get('inventory_name', '').lower()
                    if inventory_org in ('efd', 'efn', 'efl'):
                        inventory_name = 'inventory_{inventory_org}'
                        data.pop('inventory_name')
                        try:
                            result = update_inventory_item(inventory_name, data.get('item_id'), data)
                        except Exception as exc:
                            if request:
                                messages.error(request, 'Error while updating item in Zoho Inventory',)
                            print('Error while updating item in Zoho Inventory')
                            print(exc)
                            print(data)
                        else:
                            if result.get('code') == 0:
                                obj.status = 'approved'
                                obj.approved_on = timezone.now()
                                obj.approved_by = get_approved_by(user=request.user)
                                obj.save()
                                if request:
                                    messages.success(request, 'This change is approved and updated in Zoho Inventory')
                                notify_inventory_item_change_approved_task.delay(obj.id)
                            else:
                                if request:
                                    messages.error(request, 'Error while updating item in Zoho Inventory')
                                print('Error while updating item in Zoho Inventory')
                                print(result)
                                print(data)
                    else:
                        if request:
                            messages.error(request, 'Item have invalid inventory name.')
                        print('Item have invalid inventory name.')


    def cultivar_name(self, obj):
        return obj.item.cultivar.cultivar_name
