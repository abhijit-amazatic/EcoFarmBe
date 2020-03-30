from rest_framework.permissions import BasePermission

class UserPermissions(BasePermission):

    def has_permission(self, request, view):
        if view.action == 'create':
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return True


class IsAuthenticatedSitePermission(BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True

    # def has_object_permission(self, request, view, obj):
    #     """
    #     related to objects like site
    #     """
        # message = "You are not allowed to perform this"
        # if not (obj.user == request.user):
        #     return True
        # return False
