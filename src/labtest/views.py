from django.shortcuts import render
from rest_framework import (viewsets, status,)
from rest_framework.response import (Response, )
from rest_framework.filters import (OrderingFilter, )
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from .serializers import (LabTestSerializer, )
from .models import (LabTest, )

class LabTestViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (AllowAny, )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = '__all__'
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        return LabTestSerialier
    
    def get_queryset(self, sku):
        """
        Return QuerySet.
        """
        return LabTest.objects.all()