from django.contrib import admin
from django.shortcuts import HttpResponseRedirect
from django.db import models
from django import forms
from django.contrib.admin.utils import (unquote,)

from .models import CustomInventory



# Register your models here.
class CustomInventoryAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    change_form_template = "inventory/custom_inventory_change_form.html"
    list_display = ('cultivar_name', 'category_name', 'grade_estimate', 'quantity_available', 'farm_ask_price', 'status', 'created_on', 'updated_on',)
    readonly_fields = ('status', 'created_on', 'updated_on', 'cultivar_name',)
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
                'created_on',
                'updated_on',
            ),
        }),
    )

    def response_change(self, request, obj):
        if "_approve" in request.POST:
            if obj.status == 'pending_for_approval':
                try:
                    self.approve(request, obj)
                except Exception:
                    self.message_user(request, "Error in approval", level='error')
                else:
                    self.message_user(request, "This item is approved")
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

    def approve(self, request, obj):
        obj.status = 'approved'
        obj.save()

    def cultivar_name(self, obj):
            return obj.cultivar.cultivar_name

    # def test_action(self, request, queryset):
    #     pass

admin.site.register(CustomInventory, CustomInventoryAdmin)

