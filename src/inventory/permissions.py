from rest_framework import permissions


class DocumentPermission(permissions.BasePermission):

    def __init__(self):
        super().__init__()

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        elif request.method == 'DELETE' and request.user.is_authenticated:
            return True
        return False