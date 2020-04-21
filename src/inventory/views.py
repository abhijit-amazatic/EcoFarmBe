"""
Views for Inventory
"""
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import (viewsets, status,)
from rest_framework.permissions import (IsAuthenticated, )
from django_filters import rest_framework as filters
from .serializers import (InventorySerialier, )
from .models import (Inventory, )
from integration.inventory import (fetch_inventory, )

class InventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {'sku':['exact', 'contains'],
                     'category_name':['exact', 'contains'],
                     'cf_cultivar_type':['exact', 'contains'],
                     'cf_strain_name':['exact', 'contains'],
                     'price':['gte', 'lte', 'gt', 'lt'],
                     'cf_potency':['gte', 'lte', 'gt', 'lt'],
                     'available_stock':['gte', 'lte', 'gt', 'lt'],
                     'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
                     'cf_cannabis_grade_and_category':['exact', 'contains'],
                     'last_modified_time':['gte', 'lte', 'gt', 'lt']}
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        return InventorySerialier
    
    def get_queryset(self):
        """
        Return QuerySet.
        """
        fetch_inventory()
        return Inventory.objects.all()

    def create(self, request):
        """
        Create inventory
        """
        serializer = InventorySerialier(
            data=request.data, context={'request': request}, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)