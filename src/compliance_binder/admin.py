from django.contrib import admin

# Register your models here.
from integration.crm import(search_query,)
from .models import (
    BinderLicense,
)

class BinderLicenseAdmin(admin.ModelAdmin):
    """
    BinderLicenseAdmin
    """
    readonly_fields = ('created_on','updated_on',)

#     formfield_overrides = {
#         # models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
#         models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
#     }

from django.contrib import admin
from django import forms
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.utils import timezone

from django_json_widget.widgets import JSONEditorWidget

from integration.inventory import (
    get_inventory_obj,
)
from  .models import (
    BinderLicense,
)


class BinderLicenseAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'legal_business_name',
        'license_number',
        'profile_category',
        'status',
        'created_on',
        'updated_on',
    )

    readonly_fields = (
        'created_on',
        'updated_on',
    )
    write_only_fields = (
        'item',
    )

    create_fields = (
        'legal_business_name',
        'license_number',
        # 'profile_category',
    )


    fieldsets = (
        (None, {
            'fields': (
                'profile_license',
                'license_number',
                'legal_business_name',
                'license_type',
                'profile_category',
                'premises_apn',
            ),
        }),
        ('Premises Address', {
            'fields': (
                'premises_address',
                'premises_city',
                'premises_county',
                'premises_state',
                'zip_code',
            ),
        }),
        ('URLs', {
            'fields': (
                'uploaded_license_to',
                'uploaded_sellers_permit_to',
                'uploaded_w9_to',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'issue_date',
                'expiration_date',
                'is_updated_in_crm',
                'zoho_crm_id',
                'zoho_books_id',
                'status_before_expiry',
                'created_on',
                'updated_on',
            ),
        }),
    )




    # formfield_overrides = {
    #     JSONField: {'widget': JSONEditorWidget(options={'modes':['code', 'text'], 'search': True, }, attrs={'disabled': 'disabled'})},
    #     # JSONField: {'widget': JSONEditorWidget},
    # }

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
        if obj and obj.profile_license:
            return tuple(field.name for field in BinderLicense._meta.fields if field.name not in ('id', 'profile_license'))
        return self.readonly_fields


    # def has_change_permission(self, request, obj=None):
    #     return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != 'approved':
            return True
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            response = search_query('Licenses', obj.license_number, 'Name', is_license=True)
            if response.get('status_code') == 200:
                data = response.get('response', [])
                if data and isinstance(data, list):
                    data = [lic for lic in data if lic.get('Name') == obj.license_number]
                    if data:
                        lic=data[0]
                        obj.zoho_crm_id                = lic.get('id')
                        obj.license_type               = lic.get('License_Type')
                        # obj.profile_category           = lic.get('')
                        obj.premises_address           = lic.get('Premises_Address')
                        obj.premises_county            = lic.get('Premises_County')
                        obj.premises_city              = lic.get('Premises_City')
                        obj.premises_apn               = lic.get('Premises_APN_Number')
                        obj.premises_state             = lic.get('Premises_State')
                        obj.zip_code                   = lic.get('Premises_Zipcode')
                        obj.issue_date                 = lic.get('Issue_Date')
                        obj.expiration_date            = lic.get('Expiration_Date')
                        # obj.uploaded_license_to        = lic.get('')
                        # obj.uploaded_sellers_permit_to = lic.get('')
                        # obj.uploaded_w9_to             = lic.get('')
        return super().save_model(request, obj, form, change)



admin.site.register(BinderLicense, BinderLicenseAdmin)








