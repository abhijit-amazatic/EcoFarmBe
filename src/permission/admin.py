from django.contrib import admin
from django.db import models
from django.contrib.admin import widgets
from .widgets import PermissionSelectMultipleWidget
from .models import (
    Permission,
    PermissionGroup,
    InternalRole,
)


class PermissionGroupAdmin(admin.ModelAdmin):
    """
    Permission Group Admin
    """
    readonly_fields = ()

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PermissionAdmin(admin.ModelAdmin):
    """
    Permission Admin
    """
    readonly_fields = ()

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class InternalRoleAdmin(admin.ModelAdmin):
    """
    InternalRoleAdmin
    """
    readonly_fields = ('created_on','updated_on',)

    formfield_overrides = {
        models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
        # models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
    }




admin.site.register(Permission, PermissionAdmin)
admin.site.register(PermissionGroup, PermissionGroupAdmin)
admin.site.register(InternalRole, InternalRoleAdmin)
