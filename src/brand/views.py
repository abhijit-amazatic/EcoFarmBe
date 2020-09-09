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
from .models import (Brand,License,LicenseUser,ProfileContact,LicenseProfile,CultivationOverview,ProgramOverview,FinancialOverview,CropOverview,ProfileCategory,)
from .serializers import (BrandSerializer,BrandCreateSerializer,LicenseSerializer,ProfileContactSerializer,CultivationOverviewSerializer,LicenseProfileSerializer,FinancialOverviewSerializer,CropOverviewSerializer,ProgramOverviewSerializer,)


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
    permission_classes = (IsAuthenticatedBrandPermission, )
    profile_contact_path = 'profile-contact(/(?P<profile_contact_id>[0-9]*))?'
    cultivation_overview_path = 'cultivation-overview(/(?P<cultivation_overview_id>[0-9]*))?'
    license_profile_path = 'license-profile(/(?P<license_profile_id>[0-9]*))?'
    financial_overview_path = 'financial-overview(/(?P<financial_overview_id>[0-9]*))?'
    crop_overview_path = 'crop-overview(/(?P<crop_overview_id>[0-9]*))?'
    program_overview_path = 'program-overview(/(?P<program_overview_id>[0-9]*))?'
    filter_backends = [filters.SearchFilter]
    search_fields = ['status', ]


    def get_queryset(self):
        """
        Return queryset based on action.
        """
        license = License.objects.filter()
        if self.action == "list":
            print('in listv action')
            license = license.select_related('brand')
        elif self.action == "profile_contact":
            license = license.select_related('profile_contact')
        elif self.action == "cultivation_overview":
            license = license.select_related('cultivation_overview')
        elif self.action == "license_profile":
            license = license.select_related('license_profile')
        elif self.action == "financial_overview":
            license = license.select_related('financial_overview')
        elif self.action == "crop_overview":
            license = license.select_related('crop_overview')
        elif self.action == "program_overview":
            license = license.select_related('program_overview')            
        #license = license.filter(brand__ac_manager=self.request.user)
        license = license.filter(created_by=self.request.user)
        return license
    
    def get_serializer_class(self):
        """
        Return serializer on the basis of action.
        """
        if self.action == 'profile_contact':
            return ProfileContactSerializer
        elif self.action == 'cultivation_overview':
            return CultivationOverviewSerializer
        elif self.action == 'license_profile':
            return LicenseProfileSerializer
        elif self.action == 'financial_overview':
            return FinancialOverviewSerializer
        elif self.action == 'crop_overview':
            return CropOverviewSerializer
        elif self.action == 'program_overview':
            return ProgramOverviewSerializer
        return LicenseSerializer

    def create(self, request):
        """
        This is used to create Licensse.
        """
        serializer = LicenseSerializer(data=request.data, context={'request': request}, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def extra_info(self, request, pk, model, serializer, extra_info_attribute):
        """
        Generic feature for detail route.
        """
        license = self.get_object()
        if request.method == 'GET':
            try:
                return Response(serializer(
                    getattr(license, extra_info_attribute)).data)
            except model.DoesNotExist:
                return Response({})
        else:
            try:
                ser = serializer(
                    getattr(license, extra_info_attribute), data=request.data,context={'request': request},partial=True)
            except model.DoesNotExist:
                request.data['license'] = license.id
                ser = serializer(data=request.data, context={'request': request})
            ser.is_valid(raise_exception=True)
            ser.save(license=license)
            return Response(ser.data)

    @action(detail=True, url_path=profile_contact_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def profile_contact(self, request, pk,profile_contact_id=None):
        """
        Detail route CRUD operations on profile_contact.
        """
        return self.extra_info(request, pk, ProfileContact, ProfileContactSerializer, 'profile_contact')
        

    @action(detail=True, url_path=cultivation_overview_path, methods=['get','patch'], pagination_class=CustomPagination)
    def cultivation_overview(self, request, pk,cultivation_overview_id=None):
        """
        Detail route CRUD operations on cultivation_overview.
        """
        return self.extra_info(request, pk, CultivationOverview, CultivationOverviewSerializer, 'cultivation_overview')
        

    @action(detail=True, url_path=financial_overview_path, methods=['get','delete', 'patch'], pagination_class=CustomPagination)
    def financial_overview(self, request, pk,financial_overview_id=None):
        """
        Detail route CRUD operations on financial_overview.
        """
        return self.extra_info(request, pk, FinancialOverview, FinancialOverviewSerializer, 'financial_overview')

    @action(detail=True, url_path=crop_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def crop_overview(self, request, pk,crop_overview_id=None):
        """
        Detail route CRUD operations on crop_overview.
        """
        return self.extra_info(request, pk, CropOverview, CropOverviewSerializer, 'crop_overview')

    @action(detail=True, url_path=program_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def program_overview(self, request, pk,program_overview_id=None):
        """
        Detail route CRUD operations on program_overview.
        """
        return self.extra_info(request, pk, ProgramOverview, ProgramOverviewSerializer, 'program_overview')

    @action(detail=True, url_path=license_profile_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def license_profile(self, request, pk,license_profile_id=None):
        """
        Detail route CRUD operations on license_profile.
        """
        return self.extra_info(request, pk, LicenseProfile, LicenseProfileSerializer, 'license_profile')
    
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

class KpiViewSet(APIView):
    """
    All KPI view set
    """
    permission_classes = (IsAuthenticatedBrandPermission, )
    
    def get(self,request):
        """
        Return QuerySet.
        """
        license_obj = License.objects.filter(created_by=self.request.user).select_related()
        brand_obj = Brand.objects.filter(ac_manager=self.request.user)
        
        brand_kpis = [{
            'brand_id':profile.id,
            'brand_name':"N/A" if not hasattr(profile,'brand_name') else profile.brand_name,
            'brand_category': "N/A" if not hasattr(profile,'brand_category') else profile.brand_category,
            'brand_county': "N/A" if not hasattr(profile,'brand_county') else profile.brand_county,
            'profile_category':"N/A" if not hasattr(profile,'profile_category') else profile.profile_category,
            'licenses_owned':License.objects.filter(brand=profile,owner_or_manager='owner').count(),
            'licenses_managed':License.objects.filter(brand=profile,owner_or_manager='manager').count(),
            'updated_on':"N/A" if not hasattr(profile,'updated_on') else profile.updated_on,
        } for profile in brand_obj]
        
        license_profile_kpis = [{'license_id':license.id,
                                 'status':"N/A" if not hasattr(license,'status') else license.status,
                                 'step':"N/A" if not hasattr(license,'status') else license.step,
                                 'profile_category': "N/A" if not hasattr(license,'profile_category') else license.profile_category,
                                 'farm_name':"N/A" if not hasattr(license,'license_profile') else license.license_profile.farm_name,
                                 'region':"N/A" if not hasattr(license,'license_profile') else license.license_profile.region,
                                 'farm_profile_photo':"N/A" if not hasattr(license,'license_profile') else license.license_profile.farm_profile_photo,
                                 'farm_photo_sharable_link':"N/A" if not hasattr(license,'license_profile') else license.license_profile.farm_photo_sharable_link, 
                                 'updated_on':"N/A" if not hasattr(license,'updated_on') else license.updated_on
        } for license in license_obj]
        
        return Response({"brand_kpis": brand_kpis,
                         "license_profile_kpis":license_profile_kpis})
    


