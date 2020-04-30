"""
Views for Inventory
"""
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import (viewsets, status,)
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from .serializers import (InventorySerialier, LogoutInventorySerializer, )
from .models import (Inventory, )

class InventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (AllowAny, )
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {
        'name':['icontains'],
        'sku':['icontains'],
        'category_name':['icontains'],
        'cf_cultivar_type':['icontains'],
        'cf_strain_name':['icontains'],
        'price':['gte', 'lte', 'gt', 'lt'],
        'cf_potency':['gte', 'lte', 'gt', 'lt'],
        'available_stock':['gte', 'lte', 'gt', 'lt'],
        'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
        'cf_cannabis_grade_and_category':['icontains'],
        'last_modified_time':['gte', 'lte', 'gt', 'lt']
        }
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        if not self.request.user.is_authenticated:
            return LogoutInventorySerializer
        return InventorySerialier
    
    def get_queryset(self):
        """
        Return QuerySet.
        """
        return Inventory.objects.all()