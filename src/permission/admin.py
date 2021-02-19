from django.contrib import admin
from django.db import models
from django.contrib.admin import widgets
from .widgets import PermissionSelectMultipleWidget
from .models import (
    Permission,
    PermissionGroup,
    InternalRole,
)

# Register your models here.

class ProfileCategoryAdmin(admin.ModelAdmin):
    """
    ProfileCategoryAdmin
    """
    #search_fields = ('',)

class PermissionAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    readonly_fields = ()



class InternalRoleAdmin(admin.ModelAdmin):
    """
    InternalRoleAdmin
    """
    readonly_fields = ('created_on','updated_on',)

    formfield_overrides = {
        models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
        # models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
    }




admin.site.register(Permission,PermissionAdmin)
admin.site.register(PermissionGroup,admin.ModelAdmin)
admin.site.register(InternalRole,InternalRoleAdmin)
