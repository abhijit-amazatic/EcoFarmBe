from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ViewSetMixin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import View
from user.models import (User, )
from brand.permission_defaults import (
    SALES_REP_GROUP_NAME,
)



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
        if self.user.groups.filter(name=SALES_REP_GROUP_NAME).exists():
            return self.queryset
        q = Q()
        q |= Q(created_by=self.user)
        q |= Q(organization_user__user=self.user)
        return self.queryset.filter(q).distinct()

    def brand_brand(self):
        if self.user.groups.filter(name=SALES_REP_GROUP_NAME).exists():
            return self.queryset
        q = Q()
        q |= Q(organization__created_by=self.user)
        return self.queryset.filter(q).distinct()

    def brand_license(self):
        if self.user.groups.filter(name=SALES_REP_GROUP_NAME).exists():
            return self.queryset
        q = Q()
        q |= Q(organization__created_by=self.user)
        if self.view and self.view.action == 'list':
            q |= Q(organizationuserrole__organization_user__user=self.user)&Q(organizationuserrole__role__permissions='view_license')
        else:
            q |= Q(organizationuserrole__organization_user__user=self.user)
        return self.queryset.filter(q).distinct()

    def brand_organizationuser(self):
        # if self.user.groups.filter(name=SALES_REP_GROUP_NAME).exists():
        #     return self.queryset
        q = Q()
        q |= Q(organization__created_by=self.user)
        q |= Q(organization_user_role__role__permissions='view_organization_user')
        return self.queryset.filter(q).distinct()