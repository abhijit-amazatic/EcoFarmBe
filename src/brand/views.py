# pylint:disable = all
"""
This module defines API views.
"""

import json
from rest_framework.response import Response
from rest_framework import (permissions, viewsets, status, filters,)
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.conf import settings
from core.permissions import IsAuthenticatedBrandPermission
from .models import (Brand,License,LicenseUser,ProfileContact,LicenseProfile,CultivationOverview,ProgramOverview,FinancialOverview,CropOverview)
from .serializers import (BrandSerializer,BrandCreateSerializer,LicenseSerializer,)


class CustomPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'

    
class BrandViewSet(viewsets.ModelViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedBrandPermission, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['brand_name', ]
    

    def get_serializer_class(self):
        """
        Return serializer on the basis of action.
        """
        if self.action == 'create':
            return BrandCreateSerializer
        return BrandSerializer
    
    def get_queryset(self):
        """
        Return queryset based on action.
        """
        brands = Brand.objects.filter()
        if self.action == "list":
            brands = brands.select_related('ac_manager')
        brands = brands.filter(ac_manager=self.request.user)
        return brands    
        

    def create(self, request):
        """
        This endpoint is used to create Brand.
        """
        serializer = BrandCreateSerializer(
            data=request.data, context={'request': request}, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LicenseViewSet(viewsets.ModelViewSet):
    """
    All LicenseViewSet
    """
    #serializer_class = VendorProfileSerializer
    permission_classes = (IsAuthenticatedVendorPermission, )
    profile_contact_path = 'profile-contact(/(?P<profile_contact_id>[0-9]*))?'
    profile_overview_path = 'profile-overview(/(?P<profile_overview_id>[0-9]*))?'
    financial_overview_path = 'financial-overview(/(?P<financial_overview_id>[0-9]*))?'
    processing_overview_path = 'processing-overview(/(?P<processing_overview_id>[0-9]*))?'
    program_overview_path = 'program-overview(/(?P<program_overview_id>[0-9]*))?'

    
    #filter_backends = [filters.SearchFilter]
    #search_fields = ['vendor_category', ] Add this based on farm name

    def get_queryset(self):
        """
        Return queryset based on action.
        """
        vendor_profile = VendorProfile.objects.filter()
        if self.action == "list":
            vendor_profile = vendor_profile.select_related('vendor')
        elif self.action == "profile_contact":
            vendor_profile = vendor_profile.select_related('profile_contact')
        elif self.action == "profile_overview":
            vendor_profile = vendor_profile.select_related('profile_overview')
        elif self.action == "financial_overview":
            vendor_profile = vendor_profile.select_related('financial_overview')
        elif self.action == "processing_overview":
            vendor_profile = vendor_profile.select_related('processing_overview')
        elif self.action == "program_overview":
            vendor_profile = vendor_profile.select_related('program_overview')
            
        #if not self.request.user.is_staff and not self.request.user.is_superuser:
        vendor_profile = vendor_profile.filter(vendor__vendor_roles__user=self.request.user)
        #vendor_profile = vendor_profile.filter(vendor__ac_manager=self.request.user)
            
            
        return vendor_profile
    

       
    def get_serializer_class(self):
        """
        Return serializer on the basis of action.
        """
        if self.action == 'profile_contact':
            return ProfileContactSerializer
        elif self.action == 'profile_overview':
            return ProfileOverviewSerializer
        elif self.action == 'financial_overview':
            return FinancialOverviewSerializer
        elif self.action == 'processing_overview':
            return ProcessingOverviewSerializer
        elif self.action == 'program_overview':
            return ProgramOverviewSerializer
        return VendorProfileSerializer


    def extra_info(self, request, pk, model, serializer, extra_info_attribute):
        """
        Generic feature for detail route.
        """
        vendor_profile = self.get_object()
        if request.method == 'GET':
            try:
                return Response(serializer(
                    getattr(vendor_profile, extra_info_attribute)).data)
            except model.DoesNotExist:
                return Response({})
        else:
            try:
                ser = serializer(
                    getattr(vendor_profile, extra_info_attribute), data=request.data,context={'request': request},partial=True)
            except model.DoesNotExist:
                request.data['vendor_profile'] = vendor_profile.id
                ser = serializer(data=request.data, context={'request': request})
            ser.is_valid(raise_exception=True)
            ser.save(vendor_profile=vendor_profile)
            return Response(ser.data)

    @action(detail=True, url_path=profile_contact_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def profile_contact(self, request, pk,profile_contact_id=None):
        """
        Detail route CRUD operations on profile_contact.
        """
        return self.extra_info(request, pk, ProfileContact, ProfileContactSerializer, 'profile_contact')
        

    @action(detail=True, url_path=profile_overview_path, methods=['get', 'post', 'delete', 'patch'], pagination_class=CustomPagination)
    def profile_overview(self, request, pk,profile_overview_id=None):
        """
        Detail route CRUD operations on profile_overview.
        """
        return self.extra_info(request, pk, ProfileOverview, ProfileOverviewSerializer, 'profile_overview')
        


    @action(detail=True, url_path=financial_overview_path, methods=['get', 'post', 'delete', 'patch'], pagination_class=CustomPagination)
    def financial_overview(self, request, pk,financial_overview_id=None):
        """
        Detail route CRUD operations on financial_overview.
        """
        return self.extra_info(request, pk, FinancialOverview, FinancialOverviewSerializer, 'financial_overview')

    @action(detail=True, url_path=processing_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def processing_overview(self, request, pk,processing_overview_id=None):
        """
        Detail route CRUD operations on processing_overview.
        """
        return self.extra_info(request, pk, ProcessingOverview, ProcessingOverviewSerializer, 'processing_overview')

    @action(detail=True, url_path=program_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def program_overview(self, request, pk,program_overview_id=None):
        """
        Detail route CRUD operations on program_overview.
        """
        return self.extra_info(request, pk, ProgramOverview, ProgramOverviewSerializer, 'program_overview')

    
    
class ProfileCategoryView(APIView):

    """
    Get ProfileCategories information.
    """
    permission_classes = (permissions.AllowAny,)
    
    def get(self, request):
        """
        Display categories.    
        """
        queryset = ProfileCategory.objects.values('id','name')
        return Response(queryset)


