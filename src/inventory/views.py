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
from .serializers import (InventorySerializer, LogoutInventorySerializer, 
                          InventoryDetailSerializer, )
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
    cf_d_8_thc__in = CharInFilter(field_name='cf_d_8_thc', lookup_expr='in')
    cf_thca__in = CharInFilter(field_name='cf_thca', lookup_expr='in')
    cf_cbda__in = CharInFilter(field_name='cf_cbda', lookup_expr='in')
    cf_cbn__in = CharInFilter(field_name='cf_cbn', lookup_expr='in')
    cf_cbc__in = CharInFilter(field_name='cf_cbc', lookup_expr='in')
    cf_cbca__in = CharInFilter(field_name='cf_cbca', lookup_expr='in')
    cf_cbga__in = CharInFilter(field_name='cf_cbga', lookup_expr='in')
    cf_cbl__in = CharInFilter(field_name='cf_cbl', lookup_expr='in')
    cf_thcva__in = CharInFilter(field_name='cf_thcva', lookup_expr='in')
    cf_cbdv__in = CharInFilter(field_name='cf_cbdv', lookup_expr='in')
    cf_pesticide_summary__in = CharInFilter(field_name='cf_pesticide_summary', lookup_expr='in')
    cf_testing_type__in = CharInFilter(field_name='cf_testing_type', lookup_expr='in')
    cultivar = django_filters.CharFilter(method='get_cultivars')
            
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
        'cf_potency':['gte', 'lte', 'gt', 'lt'],
        'cf_cbd':['gte', 'lte', 'gt', 'lt'],
        'available_stock':['gte', 'lte', 'gt', 'lt'],
        'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
        'cf_cannabis_grade_and_category':['icontains', 'exact'],
        'last_modified_time':['gte', 'lte', 'gt', 'lt'],
        'product_type':['icontains', 'exact'],
        'cf_pesticide_summary':['icontains', 'exact'],
        'cf_d_8_thc':['gte', 'lte', 'gt', 'lt'],
        'cf_thca':['gte', 'lte', 'gt', 'lt'],
        'cf_cbda':['gte', 'lte', 'gt', 'lt'],
        'cf_cbn':['gte', 'lte', 'gt', 'lt'],
        'cf_cbc':['gte', 'lte', 'gt', 'lt'],
        'cf_cbca':['gte', 'lte', 'gt', 'lt'],
        'cf_cbga':['gte', 'lte', 'gt', 'lt'],
        'cf_cbl':['gte', 'lte', 'gt', 'lt'],
        'cf_thcva':['gte', 'lte', 'gt', 'lt'],
        'cf_cbdv':['gte', 'lte', 'gt', 'lt'],
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
        elif self.action == 'retrieve':
            return InventoryDetailSerializer
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
        record = sync_inventory(request.data.get('JSONString'))
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