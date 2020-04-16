"""
Integration views
"""
from django.http import (QueryDict, )
from rest_framework import (status,)
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from core.permissions import UserPermissions
from .models import Integration
from integration.box import(get_box_tokens, )
from integration.inventory import (get_inventory_item,
                                   get_inventory_items,)

class GetBoxTokensView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)
    
class InventoryView(APIView):
    """
    View class for Zoho inventory.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get an item.
        """        
        if request.query_params.get('item_id', None):
            item_id = request.query_params['item_id']
            return Response(get_inventory_item(item_id))
        data = get_inventory_items(params=request.query_params.dict())
        return Response(data)