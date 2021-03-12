from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ViewSetMixin
from django.views.generic import View
from django.utils.translation import ugettext_lazy as _



class ViewPermission(BasePermission):
    action_perm_map = {}
    method_perm_map = {}

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        related to objects
        """
        perm=''
        if isinstance(view, ViewSetMixin):
            perm = self.action_perm_map.get(view.action, {}).get(request.method.lower(), '')
        elif isinstance(view, View):
            perm = self.method_perm_map.get(request.method.lower(), '')
        if perm:
            return request.user.has_perm(perm, obj)
        elif request.method.lower() == 'options':
            return True
        return False
