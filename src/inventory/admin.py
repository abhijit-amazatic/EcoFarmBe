from django.contrib import admin
from django.shortcuts import HttpResponseRedirect
from django.db import models
from django import forms

from .models import CustomInventory



# Register your models here.
class CustomInventoryAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    change_form_template = "inventory/custom_inventory_change_form.html"
    readonly_fields = ('status',)
    actions = ['test_action', ]
    fieldsets = (
        (None, {
            'fields': ('cultivar', 'harvest_date', 'quantity_available', 'need_lab_testing_service', 'grade_estimate', 'cultivation_type', 'product_category', 'product_availability_date',),
        }),
        ('BATCH & QUALITY INFORMATION', {
            'fields': ('best_contact_window_start', 'best_contact_window_end', 'minimum_order_quantity', 'pricing_position', 'product_quality_notes', 'status',),
        }),
    )

    def response_change(self, request, obj):
        if "_approve" in request.POST:
            # obj.status = 'pending_for_approval'
            # obj.save()
            self.message_user(request, "This item is approved")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
                field.queryset = field.queryset.filter(status='approved')
        return field

    def test_action(self, request, queryset):
        pass


admin.site.register(CustomInventory, CustomInventoryAdmin)

