from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ViewSetMixin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import View

from user.models import (User, )



class ViewPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        related to objects
        """
        perm=''
        if isinstance(view, ViewSetMixin):
            perm = self.action_perm_map.get(view.action, {}).get(request.method.lower(), '')
        elif isinstance(view, View):
            perm = self.action_perm_map.get(request.method.lower(), '')
        if perm:
            return request.user.has_perm(perm, obj)
        elif request.method.lower() == 'options':
            return True
        return False


class LicenseViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_license',
        },
        'create': {
            'post': 'add_license',
        },
        'update': {
            'put': 'edit_license',
        },
        'partial_update': {
            'patch': 'edit_license',
        },
        'destroy': {
            'delete':'delete_license',
        },
        'existing_user_data_status': {
            'get': 'view_license',
        },
        'profile_contact': {
            'get': 'view_profile_contact',
            'patch': 'edit_profile_contact',
        },
        'cultivation_overview': {
            'get': 'view_cultivation_overview',
            'patch': 'edit_cultivation_overview',
        },
        'financial_overview': {
            'get': 'view_financial_overview',
            'patch': 'edit_financial_overview',
        },
        'crop_overview': {
            'get': 'view_crop_overview',
            'patch': 'edit_crop_overview',
        },
        'program_overview': {
            'get': 'view_program_overview',
            'patch': 'edit_program_overview',
        },
        'license_profile': {
            'get': 'view_license_profile',
            'patch': 'edit_license_profile',
        },
    }


class OrganizationViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization',
        },
        'create': {
            'post': 'add_organization',
        },
        'update': {
            'put': 'edit_organization',
        },
        'partial_update': {
            'patch': 'edit_organization',
        },
        'destroy': {
            'delete':'delete_organization',
        },
    }

class BrandViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_brand',
        },
        'create': {
            'post': 'add_brand',
        },
        'update': {
            'put': 'edit_brand',
        },
        'partial_update': {
            'patch': 'edit_brand',
        },
        'destroy': {
            'delete':'delete_brand',
        },
    }

class OrganizationRoleViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization_role',
        },
        'create': {
            'post': 'add_organization_role',
        },
        'update': {
            'put': 'edit_organization_role',
        },
        'partial_update': {
            'patch': 'edit_organization_role',
        },
        'destroy': {
            'delete':'delete_organization_role',
        },
    }

class OrganizationUserViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization_user',
        },
        'create': {
            'post': 'add_organization_user',
        },
        'update': {
            'put': 'edit_organization_user',
        },
        'partial_update': {
            'patch': 'edit_organization_user',
        },
        'destroy': {
            'delete':'delete_organization_user',
        },
    }

class OrganizationUserRoleViewSetPermission(ViewPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_organization_user_role',
        },
        'create': {
            'post': 'add_organization_user_role',
        },
        'update': {
            'put': 'edit_organization_user_role',
        },
        'partial_update': {
            'patch': 'edit_organization_user_role',
        },
        'destroy': {
            'delete':'delete_organization_user_role',
        },
    }


class filterQuerySet:
    queryset = None
    user = None
    request = None
    view = None

    def __init__(self, queryset, user, request=None, view=None):
        self.queryset = queryset
        self.user = user
        self.request = request
        self.view = view

    @classmethod
    def filter_queryset(cls, request, queryset, view):
        return cls.for_user(queryset, request.user, request=request, view=view)

    @classmethod
    def for_user(cls, queryset, user, **kwargs):
        if isinstance(queryset, QuerySet) and isinstance(user, User):
            instance = cls(queryset, user, **kwargs)
            model = queryset.model.__name__.lower()
            app_label = queryset.model._meta.app_label 
            method = getattr(instance, f'{app_label}_{model}', None)
            if method and callable(method):
                return method()
            queryset.none()
        return queryset


    def brand_organization(self):
        q = Q()
        q |= Q(created_by=self.user)
        q |= Q(organization_user__user=self.user)
        return self.queryset.filter(q)

    def brand_brand(self):
        q = Q()
        q |= Q(organization__created_by=self.user)
        return self.queryset.filter(q)

    def brand_license(self):
        q = Q()
        q |= Q(organization__created_by=self.user)
        if self.view and self.view.action == 'list':
            q |= Q(organizationuserrole__organization_user__user=self.user)&Q(organizationuserrole__role__permissions__codename='view_license')
        else:
            q |= Q(organizationuserrole__organization_user__user=self.user)
        print(q)
        return self.queryset.filter(q)
