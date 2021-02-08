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
from integration.crm import (sync_cultivars, create_records, update_records)


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
        'cultivar_type':['icontains', 'exact'],
        'thc_range':['gte', 'lte', 'gt', 'lt'],
        'cultivar_name':['icontains', 'exact'],
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

    def perform_create(self, serializer):
        instance = serializer.save()
        result = create_records('Cultivars', instance.__dict__)
        if result.get('status_code') == 201:
            try:
                data = instance.get('response', {}).get('data')
                if data and isinstance(data, list):
                    crm_id = data[0].get('details', {}).get('id')
            except Exception as exc:
                print('Error while creating Cultivar in Zoho CRM')
                print(exc)
            else:
                if crm_id:
                    instance.cultivar_crm_id = crm_id
        else:
            print('Error while creating Cultivar in Zoho CRM')
            print(result)


    def perform_update(self, serializer):
        instance = serializer.save()
        result = update_records('Cultivars', instance.__dict__)
        if not result.get('status_code') == 200:
            print('Error while creating Cultivar in Zoho CRM')
            print(result)


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