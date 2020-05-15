"""
Integration views
"""
from django.http import (QueryDict, )
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from core.permissions import UserPermissions
from .models import Integration
from integration.box import(get_box_tokens, )
from integration.inventory import (get_inventory_item,
                                   get_inventory_items,)
from integration.crm import (search_query, get_picklist,
                             list_crm_contacts, )
from integration.books import (create_contact, create_estimate,
                               get_estimate, list_estimates, 
                               get_contact, list_contacts, )

class GetBoxTokensView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)

class SearchCultivars(APIView):
    """
    Return Cultivar information from Zoho CRM.
    """
    permission_class = (IsAuthenticated, )
    
    def get(self, request):
        """
        Get Cultivar information.
        """
        data = search_query('Cultivars', request.query_params['cultivar_name'], 'Name', True)
        if data['status_code'] == 200:
            return Response(data)
        return Response({})

class GetPickListView(APIView):
    """
    Get field dropdowns from Zoho CRM.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get picklist.
        """
        return Response(get_picklist('Vendors', request.query_params['field']))

class CRMContactView(APIView):
    """
    Get Contacts from Zoho CRM.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contacts.
        """
        if request.query_params.get('contact_id'):
            return Response(list_crm_contacts(request.query_params.get('contact_id')))
        return Response(list_crm_contacts())


class InventoryView(APIView):
    """
    View class for Zoho inventory. Fetch data from Zoho Inventory.
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
    
class EstimateView(APIView):
    """
    View class for Zoho books estimates.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get estimates.
        """
        if request.query_params.get('estimate_id', None):
            return Response(get_estimate(request.query_params.get('estimate_id')))
        return Response(list_estimates(params=request.query_params.dict()))

    def post(self, request):
        """
        Create estimate in Zoho Books.
        """
        return Response(create_estimate(data=request.data, params=request.query_params.dict()))

class ContactView(APIView):
    """
    View class for Zoho books contacts.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contact.
        """
        if request.query_params.get('contact_id', None):
            return Response(get_contact(request.query_params.get('contact_id')))
        return Response(list_contacts(params=request.query_params.dict()))

    def post(self, request):
        """
        Create contact in Zoho Books.
        """
        return Response(create_contact(data=request.data, params=request.query_params.dict()))
