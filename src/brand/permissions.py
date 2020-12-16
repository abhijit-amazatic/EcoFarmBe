from rest_framework.permissions import BasePermission
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.db.models.query import QuerySet

from user.models import (User, )



class ViewSetPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        related to objects
        """
        perm = self.action_perm_map.get(view.action, {}).get(request.method.lower(), '')
        if perm:
            return request.user.has_perm(perm, obj)
        elif request.method.lower() == 'options':
            return True
        return False


class LicenseViewSetPermission(ViewSetPermission):
    action_perm_map = {
        'retrieve': {
            'get': 'view_license',
        },
        'create': {
            'post': 'add_license',
        },
        'update': {
            'put': 'change_license',
        },
        'partial_update': {
            'patch': 'change_license',
        },
        'destroy': {
            'delete':'delete_license',
        },
        'existing_user_data_status': {
            'get': 'view_license',
        },
        'profile_contact': {
            'get': 'view_profile_contact',
            'patch': 'change_profile_contact',
        },
        'cultivation_overview': {
            'get': 'view_cultivation_overview',
            'patch': 'change_cultivation_overview',
        },
        'financial_overview': {
            'get': 'view_financial_overview',
            'patch': 'change_financial_overview',
        },
        'crop_overview': {
            'get': 'view_crop_overview',
            'patch': 'change_crop_overview',
        },
        'program_overview': {
            'get': 'view_program_overview',
            'patch': 'change_program_overview',
        },
        'license_profile': {
            'get': 'view_license_profile',
            'patch': 'change_license_profile',
        },
    }


class filterQuerySet:

    def __init__(self, queryset, user):
        self.queryset = queryset
        self.user = user

    @classmethod
    def for_user(cls, queryset, user):
        if isinstance(queryset, QuerySet) and isinstance(user, User):
            instance = cls(queryset, user)
            model = queryset.model.__name__.lower()
            app_label = queryset.model._meta.app_label 
            method = getattr(instance, f'{app_label}_{model}_for_user', None)
            if method and callable(method):
                return method()
            queryset.none()
        return queryset

    def brand_organization_for_user(self):
        return self.queryset.filter(
            created_by=self.user
        )

    def brand_brand_for_user(self):
        return self.queryset.filter(
            organization__created_by=self.user
        )

    def brand_license_for_user(self):
        return self.queryset.filter(
            organization__created_by=self.user,
        )