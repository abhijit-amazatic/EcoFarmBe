from django.contrib import admin
from django.contrib import admin
from django.shortcuts import HttpResponseRedirect
from django.db import models
from django.db.models import Q
from django import forms
from django.contrib.admin.utils import (unquote,)

from integration.crm import (create_records, update_records)
from .models import Cultivar
from .tasks import (notify_slack_cultivar_added, notify_slack_cultivar_Approved)

# Register your models here.
class CultivarAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = ('cultivar_name', 'cultivar_type', 'cultivar_crm_id', 'status', 'modified_by', 'modify_time', 'created_by', 'create_time',)
    readonly_fields = ('status',)
    change_form_template = "inventory/custom_inventory_change_form.html"
    actions = ['approve_selected_cultivars', ]

    def response_change(self, request, obj):
        if "_approve" in request.POST:
            if obj.status == 'pending_for_approval':
                self.approve(request, obj)
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.status == 'pending_for_approval' and change:
            context['show_approve'] = True
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

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
