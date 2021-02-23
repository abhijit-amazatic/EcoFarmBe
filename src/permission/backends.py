from django.db import models
from rest_framework.utils import model_meta
from brand.permission_defaults import (
    SALES_REP_GROUP_NAME,
    SALES_REP_PERM,
)
from .models import (
    Permission,
)

class CustomPermissionBackend:

    def has_perm(self, user_obj, perm, obj=None):
        for role in user_obj.internal_roles.all():
            if role.permissions.filter(id=perm).exists():
                return True
        if not user_obj.is_active or user_obj.is_anonymous or obj is None:
            return False
        if obj:
            return user_obj.is_active and perm in self.get_all_permissions(user_obj, obj)
        return False

    def get_all_permissions(self, user_obj, obj=None):
        perm_set = set()
        perm_set.update(self._get_all_permissions(user_obj, obj))
        return perm_set

    def _get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is None:
            return set()
        obj_ls = [obj]
        while obj_ls:
            new_ls = []
            for o in obj_ls:
                if isinstance(o, models.Model):
                    if o.__class__.__name__ == 'License':
                        return self.get_license_role_perm(user_obj, o)
                    if o.__class__.__name__ == 'Organization':
                        return self.get_organization_user_perm(user_obj, o)
                    opts = o.__class__._meta.concrete_model._meta
                    fk_ref = model_meta._get_forward_relationships(opts)
                    for field_name in fk_ref:
                        if fk_ref[field_name].related_model._meta.app_label == 'brand':
                            new_ls.append(getattr(o, field_name))
            obj_ls = new_ls
        return set()

    def get_license_role_perm(self, user_obj, license_obj):
        organization_user_role_qs = license_obj.organizationuserrole_set.filter(
            organization_user__user=user_obj,
            organization_user__organization=license_obj.organization,
        )
        if license_obj.organization.created_by.id == user_obj.id:
            return self.get_all_perm_set()
        user_perm_set = set()
        perm_cache_name = '_license_role_perm_cache'
        for organization_user_role in organization_user_role_qs:
            if not hasattr(organization_user_role, perm_cache_name):
                role = organization_user_role.role
                permissions = role.permissions
                perms = permissions.all().values_list('id', flat=True)
                setattr(organization_user_role, perm_cache_name, set(perms))
            user_perm_set.update(getattr(organization_user_role, perm_cache_name))
        return user_perm_set

    def get_organization_user_perm(self, user_obj, organization_obj):
        if organization_obj.created_by_id == user_obj.id:
            return self.get_all_perm_set()
        return set()

    def get_all_perm_set(self):
        return set(Permission.objects.all().values_list('id', flat=True).order_by())
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