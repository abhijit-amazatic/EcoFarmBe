from django.contrib import admin
from django.db import models
from django import forms

from .models import CustomInventory

# Register your models here.
class CustomInventoryAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    readonly_fields = ('status',)


    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
                field.queryset = field.queryset.filter(status='approved')
        return field



admin.site.register(CustomInventory, CustomInventoryAdmin)
