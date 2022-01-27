import types
from datetime import (date, datetime)
from decimal import Decimal
from django.utils import timezone
from django.contrib import admin
from django.contrib import messages
from django.utils.html import mark_safe
from django_filters.utils import verbose_field_name

from core.mixins.admin import (CustomButtonMixin,)
from fee_variable.utils import (get_item_mcsp_fee,)
from utils import (get_approved_by, )

from integration.inventory import (
    update_inventory_item,
)
from ..models import (
    InventoryItemEdit,
)
from ..tasks import (
    notify_inventory_item_change_approved_task,
)
from ..utils import (get_item_tax,)
from ..data import(
    ITEM_CUSTOM_FIELD_ORG_MAP,
)
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


class InventoryItemEditAdminBase(CustomButtonMixin, admin.ModelAdmin):
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
        'item_biomass_type',
        'item_biomass_input_g',
        'item_total_batch_quantity',
        'item_mcsp_fee',
        'item_cultivation_tax',
        'item_farm_price',
        'item_farm_price',
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
                ('item_biomass_type', 'biomass_type'),
                ('item_biomass_input_g', 'biomass_input_g'),
                ('item_total_batch_quantity', 'total_batch_quantity'),
                ('item_mcsp_fee', 'mcsp_fee'),
                ('item_cultivation_tax', 'cultivation_tax'),
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

    # def __init__(self, model, *args, **kwargs):
    #     self.set_display_change_fields(model)
    #     return super().__init__(model, *args, **kwargs)

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


    def transform_data(self, data, org):
        data_type_conversion_map = {
            float: lambda v: str(v),
            date: lambda v: v.strftime("%Y-%m-%d"),
            Decimal: lambda v: f"{v.normalize():f}",
        }
        if data and org in ITEM_CUSTOM_FIELD_ORG_MAP:
            final_data = dict()
            org_cf_map = ITEM_CUSTOM_FIELD_ORG_MAP[org]
            for k, v in data.items():
                if type(v) in data_type_conversion_map:
                    v = data_type_conversion_map[type(v)](v)
                if k.startswith('cf_'):
                    if k in org_cf_map:
                        final_data[org_cf_map[k]] = v
                else:
                    final_data[k] = v
            return final_data
        return {}

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            if obj.mcsp_fee is None:
                obj.mcsp_fee = get_item_mcsp_fee(
                    obj.item.cf_vendor_name,
                    item_category=obj.item.category_name,
                    request=request,
                    farm_price=obj.farm_price
                )
            if isinstance(obj.mcsp_fee, Decimal):
                if obj.cultivation_tax is None:
                    obj.cultivation_tax = get_item_tax(
                        category_name=obj.item.category_name,
                        biomass_type=obj.biomass_type,
                        biomass_input_g=obj.biomass_input_g,
                        total_batch_output=obj.total_batch_quantity,
                        request=request,
                    )
                    # if obj.cultivation_tax is None and  obj.item.cf_cultivation_tax:
                    #     obj.cultivation_tax = obj.item.cf_cultivation_tax
                if isinstance(obj.cultivation_tax, Decimal):
                    data = obj.get_item_update_data()
                    if obj.farm_price:
                        price = Decimal(obj.farm_price) + obj.mcsp_fee + obj.cultivation_tax
                        if isinstance(price, Decimal):
                            price = f"{price.normalize():f}"
                        data['price'] = price
                        data['rate'] = price
                    inventory_org = obj.item_data.get('inventory_name', '').lower()
                    if inventory_org in ('efd', 'efn', 'efl'):
                        inventory_name = f'inventory_{inventory_org}'
                        data = self.transform_data(data, inventory_org)
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
        change_fields = tuple(
            f[1]
            for x in self.fieldsets if x[0] == 'Changes'
            for k, v in x[1].items()
            for f in v
        )
        form = super().get_form(request=request, obj=obj, change=change, **kwargs)
        if obj:
            # change_fields = ('marketplace_status', 'farm_price', 'pricing_position', 'batch_availability_date', 'payment_terms', 'payment_method',)
            for cf in change_fields:
                f = form.base_fields.get(cf)
                if f:
                    f.label = ''
        return form



def get_display_func(k, v):
    data_type_conversion_map = {
        float: lambda v: str(v) if v else None,
        date: lambda v: v.strftime("%Y-%m-%d") if v else None,
        Decimal: lambda v: f"{v.normalize():f}" if v else None,
        list: lambda v: ', '.join(v)if v else None,
    }
    def func(self, obj):
        old_val = obj.item_data.get(v)
        if type(old_val) in data_type_conversion_map:
            old_val = data_type_conversion_map[type(old_val)](old_val)

        if self.is_obj_changable(obj):
            return span_fixed(old_val)
        else:
            new_val = getattr(obj, k, None)
            if type(new_val) in data_type_conversion_map:
                new_val = data_type_conversion_map[type(new_val)](new_val)
            return span2_fixed(old_val, new_val)
    return func


def set_display_change_fields(model):

    update_fields = model.UPDATE_FIELDS
    fields = model._meta.fields
    verbose_names = {f.name: f.verbose_name or f.name.title() for f in fields}
    method_dict = dict()
    for k, v  in update_fields.items():
        display_func = get_display_func(k,v)
        display_func.short_description = verbose_names.get(k)
        method_dict[f"item_{k}"] = display_func
    return method_dict

InventoryItemEditAdmin = type(
    'InventoryItemEditAdmin',
    (InventoryItemEditAdminBase,),
    set_display_change_fields(InventoryItemEdit)
)