from decimal import Decimal
from django.utils import timezone
from django.contrib import admin
from django.contrib import messages
from django.utils.html import mark_safe

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

# str_fixed = lambda x : "{0:_<20}".format(str(x))
def span_fixed(x):
    return mark_safe(
        f'<span style="width: 10rem !important;display: inline-block;font-weight: 900;">{str(x)}</span>'
        f'<span style="width: 6rem !important;display: inline-block;text-align: right;"> to </span>'
    )

def span2_fixed(x, y):
    return mark_safe(
        f'<span style="width: 10rem !important;display: inline-block;font-weight: 900;">{str(x)}</span>'
        f'<span style="width: 6rem !important;display: inline-block;"> to </span>'
        f'<span style="width: 10rem !important;display: inline-block;font-weight: 900;">{str(y)}</span>'
    )


class InventoryItemEditAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'name',
        'sku',
        'vendor_name',
        'farm_price',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        'name',
        'sku',
        'item_marketplace_status',
        'item_farm_price',
        'item_pricing_position',
        'item_batch_availability_date',
        'item_payment_terms',
        'item_payment_method',
        'status',
        'cultivar_name',
        'vendor_name',
        'zoho_item_id',
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
                'name',
                'sku',
                'vendor_name',
                'cultivar_name',
            ),
        }),
        ('Changes', {
            'fields': (
                ('item_marketplace_status', 'marketplace_status'),
                ('item_farm_price', 'farm_price'),
                ('item_pricing_position', 'pricing_position'),
                ('item_batch_availability_date', 'batch_availability_date'),
                ('item_payment_terms', 'payment_terms'),
                ('item_payment_method', 'payment_method'),
                # 'have_minimum_order_quantity',
                # 'minimum_order_quantity',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'zoho_item_id',
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

    def is_obj_changable(self, obj):
        if obj and obj.status == 'pending_for_approval':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return self.is_obj_changable(obj)


    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """
        if self.fieldsets:
            if obj and not self.has_change_permission(request=request, obj=obj):
                return tuple(
                    (x[0], {k: [f[0] for f in v] for k, v in x[1].items()}) if x[0] == 'Changes' else (x[0], x[1])
                    for x in self.fieldsets
                )
            return self.fieldsets
        return [(None, {'fields': self.get_fields(request, obj)})]


    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            mcsp_fee = get_item_mcsp_fee(
                obj.item.cf_vendor_name,
                item_category=obj.item.category_name,
                request=request,
                farm_price=obj.item.cf_farm_price_2
            )
            if isinstance(mcsp_fee, Decimal):
                if obj.item.cf_cultivation_tax:
                    tax = obj.item.cf_cultivation_tax
                else:
                    tax = get_item_tax(
                        category_name=obj.item.category_name,
                        biomass_type=obj.item.cf_biomass,
                        biomass_input_g=obj.item.cf_raw_material_input_g,
                        total_batch_output=obj.item.cf_batch_qty_g,
                        request=request,
                    )
                if isinstance(tax, Decimal):
                    data = obj.get_item_update_data()
                    data['cf_cultivation_tax'] = tax
                    if obj.farm_price:
                        data['price'] = Decimal(obj.farm_price + mcsp_fee + tax)
                        data['rate'] = data['price']
                    inventory_org = data.get('inventory_name', '').lower()
                    if inventory_org in ('efd', 'efn', 'efl'):
                        inventory_name = f'inventory_{inventory_org}'
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

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request=request, obj=obj, change=change, **kwargs)
        if obj:
            change_fields = ('marketplace_status', 'farm_price', 'pricing_position', 'batch_availability_date', 'payment_terms', 'payment_method',)
            for cf in change_fields:
                f = form.base_fields.get(cf)
                if f:
                    f.label = ''
        return form


    def item_marketplace_status(self, obj):
        old_val = obj.item_data.get('cf_status')
        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            return span2_fixed(old_val, obj.marketplace_status)
    item_marketplace_status.short_description = 'Marketplace Status'
    allow_tags = True

    def item_farm_price(self, obj):
        old_val = obj.item_data.get('cf_farm_price_2')
        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            return span2_fixed(old_val, obj.farm_price)
    item_farm_price.short_description = 'Farm Price'
    allow_tags = True


    def item_pricing_position(self, obj):
        old_val = obj.item_data.get('cf_seller_position')
        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            return span2_fixed(old_val, obj.pricing_position)
    item_pricing_position.short_description = 'Pricing Position'
    allow_tags = True


    def item_batch_availability_date(self, obj):
        old_val = obj.item_data.get('cf_date_available')
        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            return span2_fixed(old_val, obj.batch_availability_date)
    item_batch_availability_date.short_description = 'Batch Availability Date'
    allow_tags = True


    def item_payment_terms(self, obj):
        old_val = obj.item_data.get('cf_payment_terms')
        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            return span2_fixed(old_val, obj.payment_terms)
    item_payment_terms.short_description = 'Payment Terms'
    allow_tags = True


    def item_payment_method(self, obj):
        old_val = obj.item_data.get('cf_payment_method')
        if old_val:
            old_val = ', '.join(old_val)
        else:
            old_val = None
        if obj.payment_method:
            new_val = ', '.join(obj.payment_method)
        else:
            new_val = None
        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            return span2_fixed(old_val, new_val)
    item_payment_method.short_description = 'Payment Method'
    allow_tags = True

