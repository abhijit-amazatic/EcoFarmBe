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

class InventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {
        'name':['exact', 'contains'],
        'sku':['exact', 'contains'],
        'category_name':['exact', 'contains'],
        'cf_cultivar_type':['exact', 'contains'],
        'cf_strain_name':['exact', 'contains'],
        'price':['gte', 'lte', 'gt', 'lt'],
        'cf_potency':['gte', 'lte', 'gt', 'lt'],
        'available_stock':['gte', 'lte', 'gt', 'lt'],
        'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
        'cf_cannabis_grade_and_category':['exact', 'contains'],
        'last_modified_time':['gte', 'lte', 'gt', 'lt']
        }
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        return InventorySerialier
    
    def get_queryset(self):
        """
        Return QuerySet.
        """
        return Inventory.objects.all()