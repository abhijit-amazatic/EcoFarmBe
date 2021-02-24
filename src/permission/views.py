from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    PermissionSerializer,
)
from .models import (
    Permission,
 )

# Create your views here.
class PermissionListView(APIView):
    """
    organizational permissions list view
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        Return QuerySet.
        """
        qs = Permission.objects.all()
        qs = qs.filter(type='organizational')
        value_list = qs.values_list('group__id', 'group__name').distinct()
        group_by_value = {}
        for value in value_list:
            group_by_value[value[1]] = PermissionSerializer(qs.filter(group=value[0]), many=True).data
        return Response({"permission": group_by_value})

