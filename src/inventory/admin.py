from os import urandom
from django.contrib import admin
from django.shortcuts import HttpResponseRedirect
from django.db import models
from django import forms
from django.contrib.admin.utils import (unquote,)
from django.utils import timezone
from django.utils.encoding import force_str
from django_otp.util import random_hex
from integration.inventory import (create_inventory_item, update_inventory_item, get_vendor_id)
from integration.crm import search_query
from .models import (
    Inventory,
    CustomInventory,
)


def get_category_id(category_name):
    name_id_map = {
        'ROOT': '-1',
        'Wholesale - Flower':                       '2155380000000446107',
        'In the Field':                             '2155380000000446105',
        'Flower - Tops':                            '2155380000001179966',
        'Flower - Bucked Untrimmed':                '2155380000001179970',
        'Flower - Bucked Untrimmed - Seeded':       '2155380000001179986',
        'Flower - Bucked Untrimmed - Contaminated': '2155380000001179990',
        'Flower - Small':                           '2155380000009002152',
        'Trim':                                     '2155380000001138013',
        'Packaged Goods':                           '2155380000001138015',
        'Isolates':                                 '2155380000001138017',
        'Isolates - CBD':                           '2155380000001179992',
        'Isolates - THC':                           '2155380000001187003',
        'Isolates - CBG':                           '2155380000001339007',
        'Isolates - CBN':                           '2155380000001339009',
        'Wholesale - Concentrates':                 '2155380000001138019',
        'Crude Oil':                                '2155380000001178426',
        'Crude Oil - THC':                          '2155380000001178430',
        'Crude Oil - CBD':                          '2155380000001178432',
        'Distillate Oil':                           '2155380000001178428',
        'Distillate Oil - THC':                     '2155380000001178434',
        'Distillate Oil - CBD':                     '2155380000001178436',
        'Shatter':                                  '2155380000001339001',
        'Sauce':                                    '2155380000001339003',
        'Crumble':                                  '2155380000001339005',
        'Kief':                                     '2155380000001501335',
        'Hash':                                     '2155380000009512784',
        'Lab Testing':                              '2155380000001213350',
        'Terpenes':                                 '2155380000001295002',
        'Terpenes - Cultivar Specific':             '2155380000001295004',
        'Terpenes - Cultivar Blended':              '2155380000001295006',
        'Services':                                 '2155380000001889003',
        'QC':                                       '2155380000001889005',
        'Transport':                                '2155380000004337546',
        'Secure Cash Handling':                     '2155380000004337548',
    }
    return name_id_map.get(category_name, '')



# Register your models here.
class CustomInventoryAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    change_form_template = 'inventory/custom_inventory_change_form.html'
    list_display = ('cultivar_name', 'category_name', 'grade_estimate', 'quantity_available', 'farm_ask_price', 'status', 'created_on', 'updated_on',)
    # readonly_fields = ( 'status', 'created_on', 'updated_on', 'cultivar_name', 'vendor_name', 'zoho_item_id',)
    readonly_fields = ('created_on', 'updated_on', 'cultivar_name',)
    # actions = ['test_action', ]
    fieldsets = (
        ('BATCH & QUALITY INFORMATION', {
            'fields': (
                'cultivar',
                'cultivar_name',
                'category_name',
                'quantity_available',
                'harvest_date',
                'need_lab_testing_service',
                'batch_availability_date',
                'grade_estimate',
                'product_quality_notes',
        ),
        }),
        ('PRICING INFORMATION', {
            'fields': (
                'farm_ask_price',
                'pricing_position',
                'have_minimum_order_quantity',
                'minimum_order_quantity',
            ),
        }),
        ('SAMPLE LOGISTICS (PICKUP OR DROP OFF)', {
            'fields': (
                'transportation',
                'best_contact_Day_of_week',
                'best_contact_time_from',
                'best_contact_time_to',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'vendor_name',
                'zoho_item_id',
                'created_on',
                'updated_on',
            ),
        }),
    )

    def response_change(self, request, obj):
        if '_approve' in request.POST:
            if obj.status == 'pending_for_approval':
                self.approve(request, obj)
            return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
                field.queryset = field.queryset.filter(status='approved')
        return field

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.status == 'pending_for_approval' and change:
            context['show_approve'] = True
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def date_str(self, date_obj):
        return str(date_obj.strftime('%m.%d.%Y'))

    def generate_sku(self, obj, client_code):
        sku = 'test_sku'
        sku += '_' + client_code
        sku += '_' + obj.cultivar.cultivar_name
        if obj.harvest_date:
            sku += '_' + obj.harvest_date.strftime('%m-%d-%y')
        sku += '_' + force_str(urandom(3).hex())
        return sku

    def get_client_code(self, request, obj):
        if obj.vendor_name:
            try:
                result = search_query('Vendors', obj.vendor_name, 'Vendor_Name')
            except Exception :
                self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')
            else:
                if result.get('status_code') == 200:
                    data_ls = result.get('response')
                    if data_ls and isinstance(data_ls, list):
                        for vendor in data_ls:
                            if vendor.get('Vendor_Name') == obj.vendor_name:
                                client_code = vendor.get('Client_Code')
                                if client_code:
                                    return client_code
                                else:
                                    self.message_user(request, f'client code not found for vendor \'{obj.vendor_name}\' in Zoho CRM', level='error')
                    self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                elif result.get('status_code') == 204:
                    self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                else:
                    self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')

        return None

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            client_code = self.get_client_code(request, obj)
            if client_code:
                data = {}
                data['item_type'] = 'inventory'
                data['name'] = obj.cultivar.cultivar_name
                data['cf_client_code'] = client_code
                data['sku'] = self.generate_sku(obj, client_code)
                data['unit'] = 'lb'
                if obj.category_name:
                    data['category_name'] = obj.category_name
                    data['category_id'] = get_category_id(obj.category_name)

                if obj.cultivar.cultivar_type:
                    data['cf_cultivar_type'] = obj.cultivar.cultivar_type
                data['cf_cultivar_name'] = obj.cultivar.cultivar_name
                data['cf_strain_name'] = obj.cultivar.cultivar_name
                data['cf_quantity_estimate'] = int(obj.quantity_available)
                data['cf_harvest_date'] = str(obj.harvest_date)  # not in inventor
                data['cf_date_available'] = str(obj.batch_availability_date)
                data['cf_cannabis_grade_and_category'] = obj.grade_estimate
                data['cf_batch_notes'] = obj.product_quality_notes
                data['cf_farm_price'] = str(int(obj.farm_ask_price))
                data['cf_seller_position'] = obj.pricing_position
                if obj.have_minimum_order_quantity:
                    data['cf_minimum_quantity'] = int(obj.minimum_order_quantity)
                data['cf_sample_in_house'] = 'Pending'
                data['cf_status'] = 'In-Testing'
                data['cf_cfi_published'] = False
                data['cf_vendor_name'] = obj.vendor_name

                data['product_type'] = 'goods'
                data['rate'] = obj.farm_ask_price + 154.40 # = Cost price + IFP Tier membership Fee
                data['vendor_name'] = obj.vendor_name
                data['purchase_rate'] = obj.farm_ask_price
                data['purchase_account_id'] = 2155380000000565567
                # data['purchase_account_name'] = 'Product Costs - Flower'
                data['inventory_account_id'] = 2155380000000448361
                # data['inventory_account_name'] = 'Inventory - In the Field'
                data['is_taxable'] = True

                try:
                    result = create_inventory_item(inventory_name='inventory_efd', record=data, params={})
                except Exception as exc:
                    self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                    print('Error while creating item in Zoho Inventory')
                    print(exc)
                    print(data)
                else:
                    if result.get('code') == 0:
                            item_id = result.get('item', {}).get('item_id')
                            if item_id:
                                obj.zoho_item_id = item_id
                                obj.status = 'approved'
                                obj.save()
                                self.message_user(request, 'This item is approved')
                    else:
                        self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                        print('Error while creating item in Zoho Inventory')
                        print(result)
                        print(data)

    def cultivar_name(self, obj):
            return obj.cultivar.cultivar_name

    # def test_action(self, request, queryset):
    #     pass

admin.site.register(CustomInventory, CustomInventoryAdmin)

