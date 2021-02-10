from django.contrib import admin
from django.shortcuts import HttpResponseRedirect
from django.db import models
from django import forms
from django.contrib.admin.utils import (unquote,)
from django.utils import timezone
from django.utils.encoding import force_str
from django_otp.util import random_hex
from integration.inventory import (create_inventory_item, update_inventory_item,)
from .models import (
    Inventory,
    CustomInventory,
)



# Register your models here.
class CustomInventoryAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    change_form_template = "inventory/custom_inventory_change_form.html"
    list_display = ('cultivar_name', 'category_name', 'grade_estimate', 'quantity_available', 'farm_ask_price', 'status', 'created_on', 'updated_on',)
    # readonly_fields = ( 'status', 'created_on', 'updated_on', 'cultivar_name', 'vendor_name', 'zoho_item_id',)
    readonly_fields = ('created_on', 'updated_on', 'cultivar_name',)
    # actions = ['test_action', ]
    fieldsets = (
        ('BATCH & QUALITY INFORMATION', {
            'fields': (
                'cultivar',
                'cultivar_name',
                'category_id',
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
        if "_approve" in request.POST:
            if obj.status == 'pending_for_approval':
                self.approve(request, obj)
            return HttpResponseRedirect(".")
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

    def approve(self, request, obj):
        sku = 'sku_tmp_'+force_str(random_hex(length=10))
        if obj.status == 'pending_for_approval':
            data = {
                # 'cultivar': obj.cultivar,
                'name': obj.cultivar.cultivar_name,
                'cf_cultivar_name': obj.cultivar.cultivar_name,
                'cf_cultivar_type': obj.cultivar.cultivar_type,
                'sku': sku,
                # 'category_id': obj.category_id,
                'category_name': obj.category_name,
                'cf_quantity_estimate': obj.quantity_available,
                'cf_harvest_date': self.date_str(obj.harvest_date),  # not in inventory
                'cf_available_date': self.date_str(obj.batch_availability_date),
                'cf_cannabis_grade_and_category': obj.grade_estimate,
                'cf_batch_notes': obj.product_quality_notes,
                'cf_farm_price': str(obj.farm_ask_price),
                'cf_seller_position': str(obj.pricing_position),
                'cf_minimum_quantity': str(obj.minimum_order_quantity if obj.have_minimum_order_quantity else 0.0),
                'price': str(obj.farm_ask_price + 1.0), # Calculate price = Cost price + IFP Tier membership Fee
                'cf_sample_in_house': 'Pending',
                'product_type': 'goods',
                'unit': 'lb',
                'cf_status': 'In-Testing',
                'cf_cfi_published': False,
                'vendor_name': obj.vendor_name,
                'cf_vendor_name': obj.vendor_name,
                'purchase_rate': "0.0",
                'account': '',
                'inventory_account': '',
                'item_tax_preferences': '',
            }
            try:
                result = create_inventory_item(inventory_name='inventory_efd', record=data, params={})
            except Exception as exc:
                self.message_user(request, "Error while creating item in Zoho Inventory", level='error')
                print('Error while creating Cultivar in Zoho CRM')
                print(exc)
            else:
                if result.get('code') == 0:
                        item_id = result.get('item', {}).get('item_id')
                        if item_id:
                            obj.zoho_item_id = item_id
                            obj.status = 'approved'
                            obj.save()
                            self.message_user(request, "This item is approved")
                else:
                    self.message_user(request, "Error while creating item in Zoho Inventory", level='error')
                    print('Error while creating Cultivar in Zoho CRM')
                    print(result)



    def cultivar_name(self, obj):
            return obj.cultivar.cultivar_name


    # def test_action(self, request, queryset):
    #     pass

admin.site.register(CustomInventory, CustomInventoryAdmin)

