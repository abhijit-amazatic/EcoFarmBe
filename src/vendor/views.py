# pylint:disable = all
"""
This module defines API views.
"""
import json
from rest_framework.response import Response
from rest_framework import (permissions, viewsets, status, filters,) 
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.decorators import action
from .serializers import (
    VendorSerializer, VendorCreateSerializer, )
from .models import (Vendor, VendorCategory )
from core.permissions import IsAuthenticatedVendorPermission
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.conf import settings


class CustomPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'


class VendorCategoryView(APIView):

    """
    Get Vendor Categories information.
    """
    permission_classes = (IsAuthenticatedVendorPermission,)
    
    def get(self, request):
        """
        Display categories.    
        """
        queryset = VendorCategory.objects.values('id','name')
        return Response(queryset)

    
class VendorViewSet(viewsets.ModelViewSet):
    """
    All Vendor related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedVendorPermission, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['vendor_categories', ]

    def get_serializer_class(self):
        """
        Return serializer on the basis of action.
        """
        print('+++++', self.action)
        if self.action == 'create':
            return VendorCreateSerializer
        elif self.action == 'vendor_profile':
            return VendorProfileSerializer
        return VendorSerializer
    
    def get_queryset(self):
        """
        Return queryset based on action.
        """
        vendors = Vendor.objects.filter()
        if self.action == "list":
            vendors = vendors.select_related('ac_manager')
        elif self.action == "vendor_profile":
            vendors = vendors.prefetch_related('vendor_profile')
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            #vendors = vendors.filter(vendor_roles__user=self.request.user)
            vendors = vendors.filter(ac_manager=self.request.user)
        return vendors

    def create(self, request):
        """
        This endpoint is used to create Vendor.
        """
        serializer = VendorCreateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            vendor = Vendor.objects.create(ac_manager_id=request.data['ac_manager'])
            vendor.vendor_categories.add(*request.data['vendor_categories'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    
