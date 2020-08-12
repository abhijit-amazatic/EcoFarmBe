from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import (viewsets, status,)
from rest_framework.response import (Response, )
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.permissions import (IsAuthenticated, )
from rest_framework.filters import (OrderingFilter, )
from django_filters import rest_framework as filters
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from .models import (Cultivar, )
from .serializers import (CultivarSerializer, )
from integration.crm import (sync_cultivars, )


class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):
    cultivar_name__in = CharInFilter(field_name='cultivar_name', lookup_expr='in')
    cultivar_type__in = CharInFilter(field_name='cultivar_type', lookup_expr='in')
    thc_range__in = CharInFilter(field_name='thc_range', lookup_expr='in')
    cbd_range__in = CharInFilter(field_name='cbd_range', lookup_expr='in')
    cbg_range__in = CharInFilter(field_name='cbg_range', lookup_expr='in')
    thcv_range__in = CharInFilter(field_name='thcv_range', lookup_expr='in')
    
    class Meta:
        model = Cultivar
        fields = {
        'cultivar_name':['icontains', 'exact'],
        'cultivar_type':['icontains', 'exact'],
        'thc_range':['gte', 'lte', 'gt', 'lt'],
        'cbd_range':['gte', 'lte', 'gt', 'lt'],
        'cbg_range':['gte', 'lte', 'gt', 'lt'],
        'thcv_range':['gte', 'lte', 'gt', 'lt'],
        }

class CultivarViewSet(viewsets.ModelViewSet):
    """
    Cultivar view
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = DataFilter
    ordering_fields = '__all__'
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        return CultivarSerializer
    
    def get_queryset(self):
        """
        Return QuerySet.
        """
        return Cultivar.objects.all()

class CultivarSyncView(APIView):
    """
    Real time cultivar sync.
    """
    authentication_classes = (TokenAuthentication, )
    
    def post(self, request):
        """
        Post realtime inventory updates.
        """
        record = sync_cultivars(request.data)
        return Response(record)