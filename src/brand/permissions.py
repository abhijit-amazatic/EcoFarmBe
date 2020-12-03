from rest_framework.permissions import BasePermission
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.db.models.query import QuerySet

from user.models import (User, )


class ObjectPermissions(BasePermission):

    def has_object_permission(self, request, view, obj):
        """
        related to objects
        """
        action_perm_map = {
        'retrieve':       'view',
        'create':         'add',
        'update':         'change',
        'partial_update': 'change',
        'destroy':        'delete',
        }
        if view.action in action_perm_map:
            perm = '{}.{}_{}'.format(
                obj._meta.app_label,
                action_perm_map[view.action],
                obj.__class__.__name__.lower(),
            )
            return request.user.has_perm(perm) or request.user.has_perm(perm, obj)
        else:
            return False


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