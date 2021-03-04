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
