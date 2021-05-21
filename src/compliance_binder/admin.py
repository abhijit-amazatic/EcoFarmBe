from django.contrib import admin
from django import forms
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.utils import timezone
from django_json_widget.widgets import JSONEditorWidget
from django.utils.translation import ugettext_lazy as _

from integration.crm import(search_query, update_records)
from integration.inventory import (
    get_inventory_obj,
)
from brand.models import (ProfileCategory,)
from  .models import (
    BinderLicense,
)


class BinderLicenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cat_ls = ProfileCategory.objects.values_list('name', flat=True)
        category_choices = tuple([(None, '---------')]+[(cat, _(cat.title())) for cat in  cat_ls])
        self.fields['profile_category'] = forms.ChoiceField(choices=category_choices, required=False,)

    class Meta:
        model = BinderLicense
        fields = '__all__'


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
        'status',
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
                'issue_date',
                'expiration_date',
                'license_status',
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
                'zoho_crm_id',
                'created_on',
                'updated_on',
            ),
        }),
    )


    form = BinderLicenseForm

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
        obj.license_number = obj.license_number.strip()
        if not change:
            try:
                lic_obj = BinderLicense.objects.get(license_number=obj.license_number)
            except BinderLicense.DoesNotExist:
                response = search_query('Licenses', obj.license_number, 'Name', is_license=True)
                if response.get('status_code') == 200:
                    data = response.get('response', [])
                    if data and isinstance(data, list):
                        data = [lic for lic in data if lic.get('Name') == obj.license_number]
                        if data:
                            lic=data[0]
                            obj.zoho_crm_id = lic.get('id')
                            obj.license_type = lic.get('License_Type')
                            # obj.profile_category = lic.get('')
                            obj.premises_address = lic.get('Premises_Address')
                            obj.premises_county = lic.get('Premises_County')
                            obj.premises_city = lic.get('Premises_City')
                            obj.premises_apn = lic.get('Premises_APN_Number')
                            obj.premises_state = lic.get('Premises_State')
                            obj.zip_code = lic.get('Premises_Zipcode')
                            obj.issue_date = lic.get('Issue_Date')
                            obj.expiration_date = lic.get('Expiration_Date')
                            obj.uploaded_license_to = lic.get('License_Box_Link')
                            obj.uploaded_sellers_permit_to = lic.get('Sellers_Permit_Box_Link')
                            obj.uploaded_w9_to = lic.get('W9_Box_Link')
                            obj.license_status = lic.get('License_Status')
            else:
                obj.profile_license = lic_obj
        else:
            if not obj.profile_license:
                data = {
                    k: v
                    for k, v in obj.__dict__.items()
                    if k in form.changed_data and k not in ('updated_on', 'created_on', 'Status')
                }
                if data and obj.__dict__.get('zoho_crm_id'):
                    data['id'] = obj.__dict__.get('zoho_crm_id')
                    response = update_records('Licenses', data)
                    if response.get('status_code') != 200:
                        self.message_user(
                            request=request,
                            message='Error while updating changes to CRM.',
                            level='warning'
                        )
                        print(response)
        return super().save_model(request, obj, form, change)



admin.site.register(BinderLicense, BinderLicenseAdmin)








