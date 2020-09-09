from rest_framework.permissions import BasePermission

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