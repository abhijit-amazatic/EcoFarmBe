"""
Views for Inventory
"""
from django.shortcuts import (render, )
from rest_framework.views import APIView
from rest_framework.response import (Response, )
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework import (viewsets, status,)
from rest_framework.filters import (OrderingFilter, )
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from .serializers import (InventorySerialier, LogoutInventorySerializer, )
from .models import (Inventory, )
from integration.inventory import (sync_inventory, )

class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):   
    name__in = CharInFilter(field_name='name', lookup_expr='in')
    product_type__in = CharInFilter(field_name='product_type', lookup_expr='in')
    cf_cultivar_type__in = CharInFilter(field_name='cf_cultivar_type', lookup_expr='in')
    cf_cannabis_grade_and_category__in = CharInFilter(field_name='cf_cannabis_grade_and_category', lookup_expr='in')
    cf_cbd__in = CharInFilter(field_name='cf_cbd', lookup_expr='in')
    cf_potency__in = CharInFilter(field_name='cf_potency', lookup_expr='in')
    
    class Meta:
        model = Inventory
        fields = {
        'sku':['icontains', 'exact'],
        'category_name':['icontains', 'exact'],
        'cf_cultivar_type':['icontains', 'exact'],
        'cf_strain_name':['icontains', 'exact'],
        'price':['gte', 'lte', 'gt', 'lt'],
        'cf_potency':['gte', 'lte', 'gt', 'lt'],
        'cf_cbd':['gte', 'lte', 'gt', 'lt'],
        'available_stock':['gte', 'lte', 'gt', 'lt'],
        'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
        'cf_cannabis_grade_and_category':['icontains', 'exact'],
        'last_modified_time':['gte', 'lte', 'gt', 'lt'],
        'product_type':['icontains', 'exact']
        }


class InventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (AllowAny, )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = DataFilter
    ordering_fields = '__all__'
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        if not self.request.user.is_authenticated:
            return LogoutInventorySerializer
        return InventorySerialier(many=True)
    
    def get_queryset(self):
        """
        Return QuerySet.
        """
        return Inventory.objects.filter(cf_cfi_published=True)

class InventorySyncView(APIView):
    """
    Real time inventory sync.
    """
    authentication_classes = (TokenAuthentication, )
    
    def post(self, request):
        """
        Post realtime inventory updates.
        """
        record = sync_inventory(request.data.get('JSONString'))
        return Response(record)
