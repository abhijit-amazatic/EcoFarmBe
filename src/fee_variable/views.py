"""
All views related to the Fees defined here.
"""
import json
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.viewsets import (ModelViewSet, ReadOnlyModelViewSet)
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import (filters,)
from django_filters import (FilterSet)
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from .models import *
from .serializers import *

class OrderVariableView(ReadOnlyModelViewSet):

    """
    Get Order Variables information.
    """
    permission_classes = (IsAuthenticated,)
    queryset = OrderVariable.objects.all()
    serializer_class = OrderVariableSerializer
    filter_backends = [filters.OrderingFilter,DjangoFilterBackend]
    filterset_fields = ['tier']


class CustomInventoryVariableView(ReadOnlyModelViewSet):
    """
    Get CustomInventory Variable information.
    """
    permission_classes = (IsAuthenticated,)
    queryset = CustomInventoryVariable.objects.all()
    serializer_class = CustomInventoryVariableSerializer
    filter_backends = [filters.OrderingFilter,DjangoFilterBackend]
    filterset_fields = ['tier','program_type']


class TaxVariableVariableView(ReadOnlyModelViewSet):
    """
    Get Tax Variable information.
    """
    permission_classes = (IsAuthenticated,)
    queryset = TaxVariable.objects.all()
    serializer_class =  TaxVariableVariableSerializer
    #filter_backends = [filters.OrderingFilter,DjangoFilterBackend]


class ProgramViewSet(ReadOnlyModelViewSet):
    """
    Get Tax Variable information.
    """
    permission_classes = (IsAuthenticated,)
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer


class FileLinkViewSet(ReadOnlyModelViewSet):
    """
    Get Tax Variable information.
    """
    permission_classes = (IsAuthenticated,)
    queryset = FileLink.objects.all()
    serializer_class = FileLinkSerializer
    lookup_field = 'label'
