"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from django.conf import settings
from django.db import models

import nested_admin

from integration.inventory import (get_inventory_obj, )
from .models import *



class OrderVariableAdmin(admin.ModelAdmin):
    """
    ordering variables for fees
    """

class CustomInventoryVariableAdmin(admin.ModelAdmin):
    """
    Custom Inventory Variables
    """
    list_display = ('program_type', 'tier', 'mcsp_fee_flower_tops', 'mcsp_fee_flower_smalls', 'mcsp_fee_trims', 'mcsp_fee_concentrates', 'mcsp_fee_isolates', 'mcsp_fee_terpenes', 'mcsp_fee_clones', 'updated_on', 'created_on')


class TaxVariableAdmin(admin.ModelAdmin):
    """
    Tax Variables
    """

class CampaignVariableAdmin(admin.ModelAdmin):
    """
    Zoho campaign Variables
    """

class QRCodeVariableAdmin(admin.ModelAdmin):
    """
    QR code Admin config here.
    """

class VendorInventoryDefaultAccountsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.zoho_organization:
            try:
                inv_obj = get_inventory_obj(inventory_name=f'inventory_{instance.zoho_organization}')
                resp_metadata = inv_obj.get_metadata(params={})
            except Exception as e:
                print(e)
            else:
                if resp_metadata.get('code') == 0:
                    self.fields_metadata = resp_metadata
                    self.instance.fields_metadata = resp_metadata
                self.set_fields_choices()

    def set_fields_choices(self):
        if hasattr(self, 'fields_metadata') and self.fields_metadata:
            fields_metadata = self.fields_metadata
            if fields_metadata.get('income_accounts_list'):
                sales_account_choices = tuple(
                    [(None, '---------')] + [
                        (acc['account_id'], f"({acc['account_code']}) {acc['account_name']}" if acc['account_code'] else  acc['account_name']) 
                        for acc in fields_metadata.get('income_accounts_list')
                    ]
                )
                self.fields['sales_account'] = forms.ChoiceField(choices=sales_account_choices, required=False)

            if fields_metadata.get('purchase_accounts_list'):
                purchase_account_choices = tuple(
                    [(None, '---------')] + [
                        (acc['account_id'], f"({acc['account_code']}) {acc['account_name']}" if acc['account_code'] else  acc['account_name']) 
                        for acc in fields_metadata.get('purchase_accounts_list')
                    ]
                )
                self.fields['purchase_account'] = forms.ChoiceField(choices=purchase_account_choices, required=False)

            if fields_metadata.get('inventory_accounts_list'):
                inventory_account_choices = tuple(
                    [(None, '---------')] + [
                        (acc['account_id'], f"({acc['account_code']}) {acc['account_name']}" if acc['account_code'] else  acc['account_name']) 
                        for acc in fields_metadata.get('inventory_accounts_list')
                    ]
                )
                self.fields['inventory_account'] = forms.ChoiceField(choices=inventory_account_choices, required=False)


    class Meta:
        model = VendorInventoryDefaultAccounts
        fields = '__all__'

class VendorInventoryCategoryAccountsForm(VendorInventoryDefaultAccountsForm):

    def __init__(self, *args, **kwargs):
        super(VendorInventoryDefaultAccountsForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'parent_formset') and hasattr(self.parent_formset, 'instance'):
            if hasattr(self.parent_formset.instance, 'fields_metadata') and self.parent_formset.instance.fields_metadata:
                self.fields_metadata = self.parent_formset.instance.fields_metadata
                self.set_fields_choices()

    class Meta:
        model = VendorInventoryCategoryAccounts
        fields = '__all__'



class VendorInventoryCategoryAccountsNestedAdmin(nested_admin.NestedTabularInline):
    extra = 0
    model = VendorInventoryCategoryAccounts
    readonly_fields = ('created_on','updated_on',)
    form = VendorInventoryCategoryAccountsForm

    # fieldsets = (
    #     (None, {
    #         'fields': (
    #             'zoho_organization',
    #             'sales_account',
    #             'purchase_account',
    #             'inventory_account',
    #         )
    #     }),
    # )



class VendorInventoryDefaultAccountsAdmin(nested_admin.NestedModelAdmin):
    """
    Vendor Inventory Default Accounts Admin
    """
    form = VendorInventoryDefaultAccountsForm
    inlines = [VendorInventoryCategoryAccountsNestedAdmin]
    list_display = ('zoho_organization', 'sales_account', 'purchase_account', 'inventory_account', 'updated_on', 'created_on')
    readonly_fields = ('updated_on', 'created_on')
    create_fields = ('zoho_organization',)


    fieldsets = (
        (None, {
            'fields': (
                'zoho_organization',
                'sales_account',
                'purchase_account',
                'inventory_account',
            )
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """
        fieldsets = super().get_fieldsets(request, obj=obj)
        if not obj:
            fs = tuple((x[0], {k: [f for f in v if f in self.create_fields] for k, v in x[1].items()}) for x in fieldsets)
            return ((x[0], x[1]) for x in fs if any(x[1].values()))
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)
        if obj:
            f = set(('zoho_organization',))
            f.update(readonly_fields)
            return tuple(f)
        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        request._zoho_org = obj
        return super().get_form(request, obj, **kwargs)




class AgreementAdmin(nested_admin.NestedModelAdmin):
    """
    Agreement Admin
    """
    list_display = (
        'name',
        'box_source_file_id',
    )
    pass

class ProgramProfileCategoryAgreementInline(nested_admin.NestedTabularInline):
    """
    Agreement Admin
    """
    extra = 0
    model = ProgramProfileCategoryAgreement
    readonly_fields = ('created_on','updated_on',)

class programAdmin(nested_admin.NestedModelAdmin):
    """
    Agreement Admin
    """
    inlines = [ProgramProfileCategoryAgreementInline]





admin.site.register(Agreement, AgreementAdmin)
admin.site.register(Program, programAdmin)
admin.site.register(OrderVariable, OrderVariableAdmin)
admin.site.register(CustomInventoryVariable, CustomInventoryVariableAdmin)
admin.site.register(TaxVariable, TaxVariableAdmin)
admin.site.register(CampaignVariable, CampaignVariableAdmin)
admin.site.register(QRCodeVariable, QRCodeVariableAdmin)
admin.site.register(VendorInventoryDefaultAccounts, VendorInventoryDefaultAccountsAdmin)
