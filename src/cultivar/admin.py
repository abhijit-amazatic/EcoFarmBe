from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.shortcuts import HttpResponseRedirect
from django.db import models
from django.db.models import Q
from django import forms
from brand.tasks import (insert_record_to_crm,)
from django.contrib.admin.utils import (unquote,)

from integration.crm import (create_records, update_records)
from brand.models import (NurseryOverview)
from core.mixins.admin import (CustomButtonMixin,)
from .models import Cultivar
from .tasks import (notify_slack_cultivar_added, notify_slack_cultivar_Approved)


class InlineNurseryOverviewAdmin(admin.TabularInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    extra = 0
    readonly_fields = ('name', 'license_number', 'organization')
    fields = ('name', 'license_number', 'organization')
    model = NurseryOverview.pending_cultivars.through

    verbose_name = 'Nursery Profile'
    verbose_name_plural = 'Nursery Profile'

    can_add = False
    can_delete = False

    def _has_add_permission(self, request, obj):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def name(self, obj):
        return obj.nurseryoverview.license.legal_business_name
    name.short_description = 'Name'

    def license_number(self, obj):
        return obj.nurseryoverview.license.license_number
    license_number.short_description = 'License Number'


    def organization(self, obj):
        return obj.nurseryoverview.license.organization.name
    organization.short_description = 'Organization'

# Register your models here.
class CultivarAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = ('cultivar_name', 'cultivar_type', 'cultivar_crm_id', 'status', 'modified_by', 'modify_time', 'created_by', 'create_time',)
    readonly_fields = ('status',)
    actions = ['approve_selected_cultivars', ]

    custom_buttons=('approve',)
    # custom_buttons_prop = {
    #     'approve': {
    #         'label': 'Approve',
    #         'color': '#ba2121',
    #     }
    # }

    def show_approve_button(self, request, obj,  add=False, change=False):
        return change and obj and obj.status == 'pending_for_approval'

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj=obj)
        if obj and obj.status == 'pending_for_approval':
            inline_instances.append(InlineNurseryOverviewAdmin(self.model, self.admin_site))
        return inline_instances

    def approve(self, request, obj):
        if not obj.cultivar_crm_id:
            try:
                result = create_records('Cultivars', obj.__dict__)
            except Exception as exc:
                    self.message_user(request, "Error while creating Cultivar in Zoho CRM", level='error')
                    print('Error while creating Cultivar in Zoho CRM')
                    print(exc)
            else:
                if result.get('status_code') == 201:
                        data = result.get('response', {}).get('data')
                        if data and isinstance(data, list):
                            crm_id = data[0].get('details', {}).get('id')
                            if crm_id:
                                obj.cultivar_crm_id = crm_id
                                obj.status = 'approved'
                                obj.save()
                                notify_slack_cultivar_Approved.delay(
                                    request.user.email,
                                    obj.cultivar_name,
                                    obj.cultivar_type,
                                )
                                for no_obj in obj.nursery_overview.all():
                                    if obj.cultivar_name not in no_obj.cultivars_in_production:
                                        no_obj.cultivars_in_production.append(obj.cultivar_name)
                                        no_obj.save()
                                    lic_obj = no_obj.license
                                    insert_record_to_crm.delay(
                                        record_id=lic_obj.id,
                                        is_buyer=lic_obj.is_buyer,
                                        is_seller=lic_obj.is_seller,
                                        is_update=True,
                                    )
                                    obj.nursery_overview.remove(no_obj)

                        self.message_user(request, "This item is approved")
                else:
                    self.message_user(request, "Error while creating Cultivar in Zoho CRM", level='error')
                    print('Error while creating Cultivar in Zoho CRM')
                    print(result)
        else:
            obj.status = 'approved'
            obj.save()

    def approve_selected_cultivars(self, request, queryset):
        qs = queryset.filter(status='pending_for_approval')
        qs.filter(~Q(cultivar_crm_id=None), ~Q(cultivar_crm_id='')).update(status='approved')
        for obj in qs.filter(Q(cultivar_crm_id=None)|Q(cultivar_crm_id='')).distinct():
            self.approve(request, obj)

    def save_model(self, request, obj, form, change):
        ret = super().save_model(request, obj, form, change)
        if change and form.changed_data and obj.status == 'approved':
            try:
                result = update_records('Cultivars', obj.__dict__)
            except Exception as exc:
                self.message_user(request, "Error while updating Cultivar in Zoho CRM", level='error')
                print('Error while updating Cultivar in Zoho CRM')
                print(exc)
            else:
                if not result.get('status_code') == 200:
                    self.message_user(request, "Error while updating Cultivar in Zoho CRM", level='error')
                    print('Error while updating Cultivar in Zoho CRM')
                    print(result)
        return ret


admin.site.register(Cultivar, CultivarAdmin)
