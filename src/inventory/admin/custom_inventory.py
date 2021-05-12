from os import urandom
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe

import nested_admin


from core import settings
from core.settings import (
    AWS_BUCKET,
    INVENTORY_EFD_ORGANIZATION_ID,
    INVENTORY_EFL_ORGANIZATION_ID,
    INVENTORY_EFN_ORGANIZATION_ID,
)

from integration.apps.aws import (create_presigned_url, )
from integration.inventory import (
    get_inventory_obj,
    get_user_id,
    get_item_category_id,
    get_vendor_id,
)
from integration.crm import search_query
from brand.models import (License, LicenseProfile,)
from fee_variable.utils import (get_tax_and_mcsp_fee,)
from .mixin import AdminApproveMixin
from ..models import (
    Inventory,
    CustomInventory,
    Documents,
)
from ..tasks import (create_approved_item_po, notify_inventory_item_approved_task)
from ..data import (CUSTOM_INVENTORY_ITEM_DEFAULT_ACCOUNTS, )
from .custom_inventory_helpers import (get_new_item_data, )

class InlineDocumentsAdmin(GenericStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    extra = 0
    readonly_fields = ('doc_type', 'file',)
    fields = ('doc_type', 'file',)
    model = Documents
    can_delete = False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def file(self, obj):
        url = self.url(obj)
        if url and obj.doc_type == 'item_image':
            return mark_safe(
                '<div style="max-width: 500px;">'
                f'<a href="{url}" target="_blank">'
                f'<img src="{url}" style="width: 100%;height: auto;" alt="Image"/>'
                '</a></div>'
            )
        return mark_safe(f'<a href="{url}" target="_blank">{url}</a>')
    file.short_description = 'Uploaded File'
    file.allow_tags = True

    def url(self, obj):
        """
        Return s3 item image.
        """
        if obj.box_url:
            return obj.box_url
        try:
            url = create_presigned_url(AWS_BUCKET, obj.path)
            return url.get('response')
        except Exception:
            return None


class CustomInventoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # inventory = get_inventory_obj(inventory_name='inventory_efd')
        # result = inventory.get_user()
        # if result.get('code') == 0:
        #     procurement_rep = [(o.get('email'), o.get('name')) for o in result.get('users', []) if o.get('status') in ['active', 'invited']]
        #     procurement_rep.insert(0, ('', '-------'))
        #     self.fields['procurement_rep'] = forms.ChoiceField(choices=procurement_rep, required=False)

    class Meta:
        model = CustomInventory
        fields = '__all__'


class CustomInventoryAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    form = CustomInventoryForm
    list_display = (
        'cultivar_name',
        'category_name',
        'vendor_name',
        'license_profile',
        'grade_estimate',
        'quantity_available',
        'farm_ask_price',
        'marketplace_status',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        'status',
        'cultivar_name',
        # 'vendor_name',
        'crm_vendor_id',
        # 'client_code',
        'procurement_rep',
        'zoho_item_id',
        'sku',
        'po_id',
        'po_number',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    fieldsets = (
        ('BATCH & QUALITY INFORMATION', {
            'fields': (
                'cultivar',
                # 'cultivar_name',
                'category_name',
                'marketplace_status',
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
                # 'have_minimum_order_quantity',
                # 'minimum_order_quantity',
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
        ('PAYMENT', {
            'fields': (
                'payment_terms',
                'payment_method',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'license_profile',
                'vendor_name',
                'crm_vendor_id',
                'client_code',
                'procurement_rep',
                'zoho_item_id',
                'sku',
                'po_id',
                'po_number',
                'approved_by',
                'approved_on',
                'created_by',
                'created_on',
                'updated_on',
            ),
        }),
        ('zoho Organization', {
            'fields': (
                'zoho_organization',
            ),
        }),
    )
    inlines = [InlineDocumentsAdmin,]
    # actions = ['test_action', ]

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
                field.queryset = field.queryset.filter(status='approved')
        return field

    def has_change_permission(self, request, obj=None):
        if obj and obj.status == 'pending_for_approval':
            return True
        return False

    def generate_sku(self, obj, postfix):
        sku = []
        if not settings.PRODUCTION and obj.zoho_organization in ['efl', 'efn']:
            sku.append('test')
            sku.append('sku')
        sku.append(obj.client_code)
        sku.append(obj.cultivar.cultivar_name.replace(' ', '-'))

        if obj.harvest_date:
            sku.append(obj.harvest_date.strftime('%m-%d-%y'))

        if postfix:
            sku.append(str(postfix))

        # if not settings.PRODUCTION:
        #     sku.append(force_str(urandom(3).hex()))

        return '-'.join(sku)

    def get_crm_data(self, request, obj):
        found_code = False
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
                                if not obj.crm_vendor_id:
                                    obj.crm_vendor_id = vendor.get('id', '')
                                if not obj.procurement_rep:
                                    p_rep = vendor.get('Owner', {}).get('email')
                                    if p_rep:
                                        obj.procurement_rep = p_rep
                                    p_rep_name = vendor.get('Owner', {}).get('name')
                                    if p_rep_name:
                                        obj.procurement_rep_name = p_rep_name
                                client_code = vendor.get('Client_Code')
                                if client_code:
                                    found_code = True
                                    obj.client_code = client_code
                                    return client_code

                if result.get('status_code') == 204 or not found_code:
                    try:
                        result = search_query('Accounts', obj.vendor_name, 'Account_Name')
                    except Exception:
                        self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')
                    else:
                        if result.get('status_code') == 200:
                            data_ls = result.get('response')
                            if data_ls and isinstance(data_ls, list):
                                for vendor in data_ls:
                                    if vendor.get('Account_Name') == obj.vendor_name:
                                        if not obj.procurement_rep:
                                            p_rep = vendor.get('Owner', {}).get('email')
                                            if p_rep:
                                                obj.procurement_rep = p_rep
                                            p_rep_name = vendor.get('Owner', {}).get('name')
                                            if p_rep_name:
                                                obj.procurement_rep_name = p_rep_name
                                        client_code = vendor.get('Client_Code')
                                        if client_code:
                                            obj.client_code = client_code
                                            return client_code
                                        else:
                                            self.message_user(request, f'client code not found for vendor \'{obj.vendor_name}\' in Zoho CRM', level='error')
                                self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                        elif result.get('status_code') == 204 or not found_code:
                            self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                else:
                    self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')

        return None

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            tax_and_mcsp_fee = get_tax_and_mcsp_fee(obj.vendor_name, request,)
            if tax_and_mcsp_fee:
                if not obj.client_code or not obj.procurement_rep or not obj.crm_vendor_id:
                    self.get_crm_data(request, obj)
                if obj.client_code:
                    if obj.zoho_organization:
                        inv_obj = get_inventory_obj(inventory_name=f'inventory_{obj.zoho_organization}')
                        category_id = get_item_category_id(inv_obj.ORGANIZATION_ID, obj.category_name)
                        if category_id:
                            if obj.vendor_name:
                                vendor_id = get_vendor_id(inv_obj, obj.vendor_name)
                                if vendor_id:
                                    data = get_new_item_data(obj, inv_obj, category_id, vendor_id, tax_and_mcsp_fee)
                                    self._approve(request, obj, inv_obj, data,)
                                else:
                                    self.message_user(request, 'Vendor not found on zoho', level='error')
                            else:
                                self.message_user(request, 'Vendor Name is not set', level='error')
                        else:
                            self.message_user(request, 'Invalid item category for selected Zoho inventory Organization', level='error')


    def _approve(self, request, obj, inv_obj, data, sku_postfix=0):
        sku = self.generate_sku(obj, sku_postfix)
        data['sku'] = sku
        try:
            result = inv_obj.create_item(data, params={})
        except Exception as exc:
            self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
            print('Error while creating item in Zoho Inventory')
            print(exc)
            print(data)
        else:
            if result.get('code') == 0:
                item_id = result.get('item', {}).get('item_id')
                if item_id:
                    obj.status = 'approved'
                    obj.zoho_item_id = item_id
                    obj.sku = sku
                    obj.approved_on = timezone.now()
                    obj.approved_by = {
                        'email': request.user.email,
                        'phone': request.user.phone.as_e164,
                        'name': request.user.get_full_name(),
                    }
                    obj.save()
                    self.message_user(request, 'This item is approved', level='success')
                    if obj.marketplace_status in ('In-Testing', 'Available'):
                        if settings.PRODUCTION or obj.zoho_organization in ['efd',]:
                            create_approved_item_po.delay(obj.id)
                        notify_inventory_item_approved_task.delay(obj.id)
                    else:
                        notify_inventory_item_approved_task.delay(obj.id, notify_logistics=False)

            elif result.get('code') == 1001 and 'SKU' in result.get('message', '') and sku in result.get('message', ''):
                self._approve(request, obj, inv_obj, data, sku_postfix=sku_postfix+1)
            else:
                msg = result.get('message')
                if msg:
                    self.message_user(request, f'Error while creating item in Zoho Inventory:  {msg}', level='error')
                else:
                    self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                print('Error while creating item in Zoho Inventory')
                print(result)
                print(data)

    def cultivar_name(self, obj):
            return obj.cultivar.cultivar_name

    # def test_action(self, request, queryset):
    #     pass
