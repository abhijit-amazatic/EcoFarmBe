"""
Views for Inventory
"""
import django_filters
from django.shortcuts import (render, )
from rest_framework.views import APIView
from rest_framework.response import (Response, )
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework import (viewsets, status,)
from rest_framework.filters import (OrderingFilter, )
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from .serializers import (InventorySerializer, LogoutInventorySerializer, )
from .models import (Inventory, )
from integration.inventory import (sync_inventory, )

class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):   
    name__in = CharInFilter(field_name='name', lookup_expr='in')
    product_type__in = CharInFilter(field_name='product_type', lookup_expr='in')
    cf_cultivar_type__in = CharInFilter(field_name='cf_cultivar_type', lookup_expr='in')
    cf_cannabis_grade_and_category__in = CharInFilter(field_name='cf_cannabis_grade_and_category', lookup_expr='in')
    cf_pesticide_summary__in = CharInFilter(field_name='cf_pesticide_summary', lookup_expr='in')
    cf_testing_type__in = CharInFilter(field_name='cf_testing_type', lookup_expr='in')
    cf_status__in = CharInFilter(field_name='cf_status', lookup_expr='in')
    cf_quantity_estimate__in = CharInFilter(field_name='cf_status', lookup_expr='in')
    cultivar = django_filters.CharFilter(method='get_cultivars')
    labtest__CBD__in = CharInFilter(field_name='labtest__CBD', lookup_expr='in')
    labtest__THC__in = CharInFilter(field_name='labtest__THC', lookup_expr='in')
    labtest__d_8_THC__in = CharInFilter(field_name='labtest__d_8_THC', lookup_expr='in')
    labtest__THCA__in = CharInFilter(field_name='labtest__THCA', lookup_expr='in')
    labtest__CBDA__in = CharInFilter(field_name='labtest__CBDA', lookup_expr='in')
    labtest__CBN__in = CharInFilter(field_name='labtest__CBN', lookup_expr='in')
    labtest__CBC__in = CharInFilter(field_name='labtest__CBC', lookup_expr='in')
    labtest__CBCA__in = CharInFilter(field_name='labtest__CBCA', lookup_expr='in')
    labtest__CBGA__in = CharInFilter(field_name='labtest__CBGA', lookup_expr='in')
    labtest__CBL__in = CharInFilter(field_name='labtest__CBL', lookup_expr='in')
    labtest__THCVA__in = CharInFilter(field_name='labtest__THCVA', lookup_expr='in')
    labtest__CBDV__in = CharInFilter(field_name='labtest__CBDV', lookup_expr='in')
            
    def get_cultivars(self, queryset, name, value):
        items = queryset.filter(
            cf_strain_name__icontains=value).filter(cf_cfi_published=True)
        return items
    
    class Meta:
        model = Inventory
        fields = {
        'sku':['icontains', 'exact'],
        'category_name':['icontains', 'exact'],
        'cf_cultivar_type':['icontains', 'exact'],
        'cf_strain_name':['icontains', 'exact'],
        'price':['gte', 'lte', 'gt', 'lt'],
        'available_stock':['gte', 'lte', 'gt', 'lt'],
        'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
        'cf_cannabis_grade_and_category':['icontains', 'exact'],
        'last_modified_time':['gte', 'lte', 'gt', 'lt'],
        'product_type':['icontains', 'exact'],
        'cf_pesticide_summary':['icontains', 'exact'],
        'cf_status':['icontains', 'exact'],
        'labtest__THC':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBD':['gte', 'lte', 'gt', 'lt'],
        'labtest__d_8_THC':['gte', 'lte', 'gt', 'lt'],
        'labtest__THCA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBDA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBN':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBC':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBCA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBGA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBL':['gte', 'lte', 'gt', 'lt'],
        'labtest__THCVA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBDV':['gte', 'lte', 'gt', 'lt'],
        'cf_quantity_estimate': ['gte', 'lte', 'gt', 'lt'],
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
        return InventorySerializer
    
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
        record = sync_inventory(
            request.data.get('inventory_name'),
            request.data.get('JSONString'))
        return Response(record)

class CultivarCategoryView(APIView):
    """
    Return distinct cultivar categroies.
    """
    def get(self, request):
        """
        Return QuerySet.
        """
        if request.query_params.get('cultivar_name'):
            categories = Inventory.objects.filter(
                cf_cfi_published=True,
                cf_strain_name__icontains=request.query_params.get('cultivar_name')
                ).values('cf_strain_name').distinct()
        else:
            categories = Inventory.objects.filter(
                cf_cfi_published=True,
                ).values('cf_strain_name').distinct()
        return Response({
            'status_code': 200,
            'response': [{
                'label': i['cf_strain_name'],
                'value': i['cf_strain_name']} for i in categories if i['cf_strain_name'] != None]})

class InventoryStatusTypeView(APIView):
    """
    Return distinct status types.
    """
    def get(self, request):
        """
        Return distinct status types.
        """
        categories = Inventory.objects.filter(
                cf_cfi_published=True
                ).values('cf_status').distinct()
        return Response({
            'status_code': 200,
            'response': [i['cf_status'] for i in categories]})
