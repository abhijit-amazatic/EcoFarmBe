from django.db import models
from rest_framework.utils import model_meta
from .models import (
    License,
    LicenseUser,
    LicenseRole,
    LicenseRolePermissions,
)

class LicensePermissionBackend:
    def has_perm(self, user_obj, perm, obj=None):
        if obj:
            return user_obj.is_active and perm in self.get_all_permissions(user_obj, obj)
        return False

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is None:
            return set()
        obj_ls = [obj]
        while obj_ls:
            new_ls = []
            for o in obj_ls:
                if isinstance(o, models.Model):
                    if o.__class__ == License:
                        return self.get_license_user_role_perm(user_obj, o)
                    opts = o.__class__._meta.concrete_model._meta
                    fk_ref = model_meta._get_forward_relationships(opts)
                    for field_name in fk_ref:
                        if fk_ref[field_name].related_model._meta.app_label == 'brand':
                            new_ls.append(getattr(o, field_name))
            obj_ls = new_ls
        return set()

    def get_license_user_role_perm(self, user_obj, license_obj):
        license_users = LicenseUser.objects.filter(license=license_obj, user=user_obj)
        user_perm_set = set()
        perm_cache_name = '_license_role_perm_cache'
        for license_user in license_users:
            if not hasattr(license_user, perm_cache_name):
                role = license_user.role
                try:
                    license_role_perm = LicenseRolePermissions.objects.get(license=license_obj, role=role)
                    permissions = license_role_perm.permissions
                except LicenseRolePermissions.DoesNotExist:
                    permissions = role.default_permissions
                perms = permissions.all().values_list('content_type__app_label', 'codename').order_by()  
                setattr(license_user, perm_cache_name, {"%s.%s" % (ct, name) for ct, name in perms})
            user_perm_set.update(getattr(license_user, perm_cache_name))
        return user_perm_set

    def authenticate(self, request, **kwargs):
        return None

    def get_user(self, user_id):
        return None

    def get_user_permissions(self, user_obj, obj=None):
        return set()

    def get_group_permissions(self, user_obj, obj=None):
        return set()

    # def get_all_permissions(self, user_obj, obj=None):
    #     return {
    #         *self.get_user_permissions(user_obj, obj=obj),
    #         *self.get_group_permissions(user_obj, obj=obj),
    #     }

    # def has_perm(self, user_obj, perm, obj=None):
    #     return perm in self.get_all_permissions(user_obj, obj=obj)