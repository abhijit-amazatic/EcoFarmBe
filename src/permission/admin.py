from django.contrib import admin
# from django.contrib.auth import get_user_model
from django.db import models
from django import forms
from django.contrib.admin import widgets
from .widgets import PermissionSelectMultipleWidget
from .models import (
    Permission,
    PermissionGroup,
    InternalRole,
)

# User = get_user_model()

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


# class InlineUserAdmin(admin.TabularInline):
#     """
#     Configuring field admin view for ProfileContact model.
#     """
#     extra = 0
#     # readonly_fields = ('email', 'full_name', 'phone',)
#     # fields = ('user__email', 'user__full_name', 'user__phone',)
#     # fields = ('__all__',)
#     exclude = ()
#     search_fields = ('user__email',)
#     model = User.internal_roles.through


class InternalRoleAdminForm(forms.ModelForm):
  class Meta:
    model = InternalRole
    widgets = {
      'permissions': PermissionSelectMultipleWidget(),
    }
    fields = '__all__'


class InternalRoleAdmin(admin.ModelAdmin):
    """
    InternalRoleAdmin
    """
    # inlines = (InlineUserAdmin,)
    change_form_template = 'permission/internal_role_change_form.html'
    form = InternalRoleAdminForm
    readonly_fields = ('created_on','updated_on',)
    filter_horizontal = ('profile_categories', 'role_users')

    # formfield_overrides = {
    #     models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
    #     # models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
    # }


admin.site.register(Permission, PermissionAdmin)
admin.site.register(PermissionGroup, PermissionGroupAdmin)
admin.site.register(InternalRole, InternalRoleAdmin)
