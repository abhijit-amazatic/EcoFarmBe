from django.contrib import admin
from django.db import models
from django import forms

from .models import Cultivar

# Register your models here.
class CultivarAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = ('cultivar_name', 'cultivar_type', 'status', 'modified_by', 'modify_time', 'created_by', 'create_time',)

    # readonly_fields = ('status',)


admin.site.register(Cultivar, CultivarAdmin)
