from os import urandom
from django import forms
from django.contrib.admin import widgets
from django.contrib import admin
from django.contrib.admin.utils import (unquote,)
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe

from simple_history.admin import SimpleHistoryAdmin
import nested_admin


from core import settings
from core.settings import (AWS_BUCKET, )

from integration.apps.aws import (create_presigned_url, )
from integration.inventory import (create_inventory_item, update_inventory_item, get_vendor_id, get_inventory_obj)
from integration.crm import search_query
from brand.models import (License, LicenseProfile,)
from fee_variable.models import (CustomInventoryVariable, TaxVariable)
from ..tasks import (create_approved_item_po, notify_inventory_item_approved)
from ..models import (
    Inventory,
    CustomInventory,
    Documents,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
    InventoryItemsChangeRequest,
)
from .custom_inventory import CustomInventoryAdmin
from import_export import resources
from import_export.admin import (ImportExportModelAdmin,ExportActionMixin)




class InventoryItemsChangeRequestAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    change_form_template = 'inventory/custom_inventory_change_form.html'
    list_display = (
        'item',
        'quantity_available',
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
    # inlines = [InlineDocumentsAdmin,]
    # actions = ['test_action', ]
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

    def response_change(self, request, obj):
        if '_approve' in request.POST:
            if obj.status == 'pending_for_approval':
                self.approve(request, obj)
            return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    #     field = super().formfield_for_foreignkey(db_field, request, **kwargs)
    #     if db_field.name == 'cultivar':
    #             field.queryset = field.queryset.filter(status='approved')
    #     return field

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.status == 'pending_for_approval' and change:
            context['show_approve'] = True
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def tax_and_mcsp_fee(self, request, obj):
        lp = LicenseProfile.objects.filter(name=obj.item.cf_vendor_name).first()
        if lp:
            if lp.license.status == 'approved':
                program_name = None
                try:
                    program_overview = lp.license.program_overview
                    program_name = program_overview.program_details.get('program_name')
                except License.program_overview.RelatedObjectDoesNotExist:
                    pass
                    # self.message_user(request, 'program overview not exist', level='error')
                if not program_name:
                    if lp.license.is_buyer:
                        program_name = 'IBP No Tier'
                    else:
                        program_name = 'IFP No Tier'
                    self.message_user(request, f'No program tier found for profile, using {program_name} MCSP fee.', level='warning')

                tier = custom_inventory_variable_program_map.get(program_name, {})
                InventoryVariable = CustomInventoryVariable.objects.filter(**tier).order_by('-created_on').first()
                if InventoryVariable and getattr(InventoryVariable, 'mcsp_fee'):
                    tax_var = TaxVariable.objects.latest('-created_on')
                    if tax_var and tax_var.cultivar_tax:
                        return float(InventoryVariable.mcsp_fee)+float(tax_var.cultivar_tax)
                    else:
                        self.message_user(request, 'No Cultivar Tax found.', level='error')
                else:
                    program_type_choices_dict = dict(CustomInventoryVariable.PROGRAM_TYPE_CHOICES)
                    program_tier_choices_dict = dict(CustomInventoryVariable.PROGRAM_TIER_CHOICES)
                    self.message_user(
                        request,
                        (
                            'MCSP fee not found in Vendor Inventory Variables for '
                            f"Program Type: '{program_type_choices_dict.get(tier.get('program_type'))}' "
                            f"and Program Tier: '{program_tier_choices_dict.get(tier.get('tier'))}'."
                        ),
                        level='error')

            else:
                self.message_user(request, 'Profile is not approved.', level='error')
        else:
            self.message_user(request, f'Profile not found for vendor name \'{obj.item.cf_vendor_name}.\'', level='error')


    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            tax_and_mcsp_fee = self.tax_and_mcsp_fee(request, obj)
            if tax_and_mcsp_fee:
                data = obj.get_item_update_data()
                if obj.farm_price:
                    data['price'] = obj.farm_price + tax_and_mcsp_fee
                inventory_name = 'inventory_efd' if data.get('inventory_name') == 'EFD' else 'inventory_efl'
                data.pop('inventory_name')
                try:
                    result = update_inventory_item(inventory_name, data.get('item_id'), data)
                except Exception as exc:
                    self.message_user(request, 'Error while updating item in Zoho Inventory', level='error')
                    print('Error while updating item in Zoho Inventory')
                    print(exc)
                    print(data)
                else:
                    if result.get('code') == 0:
                        obj.status = 'approved'
                        obj.approved_on = timezone.now()
                        obj.approved_by = {
                            'email': request.user.email,
                            'phone': request.user.phone.as_e164,
                            'name': request.user.get_full_name(),
                        }
                        obj.save()
                        self.message_user(request, 'This change is approved and updated in', level='success')
                        # create_approved_item_po.apply_async((obj.id,), countdown=5)
                        # notify_inventory_item_approved.delay(obj.id)
                    else:
                        self.message_user(request, 'Error while updating item in Zoho Inventory', level='error')
                        print('Error while updating item in Zoho Inventory')
                        print(result)
                        print(data)

    def cultivar_name(self, obj):
            return obj.item.cultivar.cultivar_name
