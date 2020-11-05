# pylint:disable = all
"""
This module defines API views.
"""

import json
import re
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import (permissions, viewsets, status, filters,)


from core.permissions import IsAuthenticatedBrandPermission

from .models import (Brand, License, LicenseUser, ProfileContact, LicenseProfile, CultivationOverview,
                     ProgramOverview, FinancialOverview, CropOverview, ProfileCategory, ProfileReport,)
from .serializers import (BrandSerializer, BrandCreateSerializer, LicenseSerializer, ProfileContactSerializer, CultivationOverviewSerializer,
                          LicenseProfileSerializer, FinancialOverviewSerializer, CropOverviewSerializer, ProgramOverviewSerializer, ProfileReportSerializer, FileUploadSerializer)
from integration.crm import (get_licenses,)
from core.utility import (get_license_from_crm_insert_to_db,)



def get_license_numbers(legal_business_names):
    """
    return license numbers based on legal business names
    """
    license_nos = []
    if legal_business_names:
        for business in legal_business_names:
            response = get_licenses(business)
            license_nos.extend([i.get('Name') for i in response])
        return license_nos
    

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


class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
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
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    search_fields = ['status', 'profile_category']
    filterset_fields = ['profile_category', 'legal_business_name']


    def get_queryset(self):
        """
        Return queryset based on action.
        """
        license = License.objects.filter()
        if self.action == "list":
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
        serializer = LicenseSerializer(data=request.data, context={
                                       'request': request}, many=True)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save()
            try:                
                if serializer.validated_data[0].get('created_by').existing_member:
                    existing_user_license_nos = get_license_numbers(serializer.validated_data[0].get('created_by').legal_business_name)
                    if serializer.validated_data[0].get('license_number') in existing_user_license_nos:
                        get_license_from_crm_insert_to_db(serializer.validated_data[0].get('created_by').id,
                                                          serializer.validated_data[0].get('license_number'),
                                                          instance[0].id)
            except Exception as e:
                print('Exception while creating& pulling existing user license',e)
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
                    getattr(license, extra_info_attribute), data=request.data, context={'request': request}, partial=True)
            except model.DoesNotExist:
                request.data['license'] = license.id
                ser = serializer(data=request.data, context={
                                 'request': request})
            ser.is_valid(raise_exception=True)
            ser.save(license=license)
            return Response(ser.data)

    @action(detail=True, url_path='existing-user-data-status', methods=['get'])
    def existing_user_data_status(self, request, pk):
        """
        existing user data status
        """
        license_obj = self.get_object()
        return Response({"is_data_fetching_complete":license_obj.is_data_fetching_complete})

    
    @action(detail=True, url_path=profile_contact_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def profile_contact(self, request, pk, profile_contact_id=None):
        """
        Detail route CRUD operations on profile_contact.
        """
        return self.extra_info(request, pk, ProfileContact, ProfileContactSerializer, 'profile_contact')

    @action(detail=True, url_path=cultivation_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def cultivation_overview(self, request, pk, cultivation_overview_id=None):
        """
        Detail route CRUD operations on cultivation_overview.
        """
        return self.extra_info(request, pk, CultivationOverview, CultivationOverviewSerializer, 'cultivation_overview')

    @action(detail=True, url_path=financial_overview_path, methods=['get', 'delete', 'patch'], pagination_class=CustomPagination)
    def financial_overview(self, request, pk, financial_overview_id=None):
        """
        Detail route CRUD operations on financial_overview.
        """
        return self.extra_info(request, pk, FinancialOverview, FinancialOverviewSerializer, 'financial_overview')

    @action(detail=True, url_path=crop_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def crop_overview(self, request, pk, crop_overview_id=None):
        """
        Detail route CRUD operations on crop_overview.
        """
        return self.extra_info(request, pk, CropOverview, CropOverviewSerializer, 'crop_overview')

    @action(detail=True, url_path=program_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def program_overview(self, request, pk, program_overview_id=None):
        """
        Detail route CRUD operations on program_overview.
        """
        return self.extra_info(request, pk, ProgramOverview, ProgramOverviewSerializer, 'program_overview')

    @action(detail=True, url_path=license_profile_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def license_profile(self, request, pk, license_profile_id=None):
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
        queryset = ProfileCategory.objects.values('id', 'name')
        return Response(queryset)


class KpiViewSet(APIView):
    """
    All KPI view set
    """
    permission_classes = (IsAuthenticatedBrandPermission, )

    def get(self, request):
        """
        Return QuerySet.
        """
        value_list = License.objects.filter(created_by=self.request.user).values_list(
            'profile_category', flat=True).distinct()
        group_by_value = {}
        for value in value_list:
            license_obj = License.objects.filter(
                created_by=self.request.user, profile_category=value).select_related()
            #license_profile_kpis = license_obj.values()
            license_profile_kpis = [{
                'id': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.id,
                'name': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.name,
                'county': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.county,
                'appellation': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.appellation,
                'ethics_and_certification': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.ethics_and_certification,
                'region': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.region,
                'product_of_interest': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.product_of_interest,
                'cultivars_of_interest': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.cultivars_of_interest,
                'about': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.about,
                'other_distributors': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.other_distributors,
                'transportation': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.transportation,
                'issues_with_failed_labtest': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.issues_with_failed_labtest,
                'preferred_payment': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.preferred_payment,
                'approved_on': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.approved_on,
                'approved_by': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.approved_by,
                'agreement_signed': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.agreement_signed,
                'agreement_link': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.agreement_link,
                'farm_profile_photo': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.farm_profile_photo,
                'farm_photo_sharable_link': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.farm_photo_sharable_link,
                'is_updated_in_crm': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.is_updated_in_crm,
                'zoho_crm_id': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.zoho_crm_id,
                'is_draft': "N/A" if not hasattr(license, 'license_profile') else license.license_profile.is_draft,
                'brand': "N/A" if not hasattr(license, 'brand') else {
                    'id': "N/A" if not hasattr(license.brand, 'id')else license.brand.id,
                    'brand_name': "N/A" if not hasattr(license.brand, 'brand_name') else license.brand.brand_name,
                    'brand_category': "N/A" if not hasattr(license.brand, 'brand_category') else license.brand.brand_category,
                    'brand_county': "N/A" if not hasattr(license.brand, 'brand_county') else license.brand.brand_county,
                    'profile_category': "N/A" if not hasattr(license.brand, 'profile_category') else license.brand.profile_category,
                    'licenses_owned': License.objects.filter(brand=license.brand, owner_or_manager='owner').count(),
                    'licenses_managed': License.objects.filter(brand=license.brand, owner_or_manager='manager').count(),
                    'updated_on': "N/A" if not hasattr(license.brand, 'updated_on') else license.brand.updated_on,
                    'is_buyer': "N/A" if not hasattr(license.brand, 'is_buyer') else license.brand.is_buyer,
                    'is_seller': "N/A" if not hasattr(license.brand, 'is_seller') else license.brand.is_seller,
                },
                'license': {
                    'id': license.id,
                    'status': "N/A" if not hasattr(license, 'status') else license.status,
                    'step': "N/A" if not hasattr(license, 'status') else license.step,
                    'is_buyer': "N/A" if not hasattr(license, 'is_buyer') else license.is_buyer,
                    'is_seller': "N/A" if not hasattr(license, 'is_seller') else license.is_seller,
                    'updated_on': "N/A" if not hasattr(license, 'updated_on') else license.updated_on,
                    'created_on': "N/A" if not hasattr(license, 'created_on') else license.created_on,
                    'license_type': "N/A" if not hasattr(license, 'license_type') else license.license_type,
                    'owner_or_manager': "N/A" if not hasattr(license, 'owner_or_manager') else license.owner_or_manager,
                    'legal_business_name': "N/A" if not hasattr(license, 'legal_business_name') else license.legal_business_name,
                    'license_number': "N/A" if not hasattr(license, 'license_number') else license.license_number,
                    'expiration_date': "N/A" if not hasattr(license, 'expiration_date') else license.expiration_date,
                    'issue_date': "N/A" if not hasattr(license, 'issue_date') else license.issue_date,
                    'premises_address': "N/A" if not hasattr(license, 'premises_address') else license.premises_address,
                    'premises_city': "N/A" if not hasattr(license, 'premises_city') else license.premises_city,
                    'premises_county': "N/A" if not hasattr(license, 'premises_county') else license.premises_county,
                    'zip_code': "N/A" if not hasattr(license, 'zip_code') else license.zip_code,
                    'premises_apn': "N/A" if not hasattr(license, 'premises_apn') else license.premises_apn,
                    'premises_state': "N/A" if not hasattr(license, 'premises_state') else license.premises_state,
                    'uploaded_license_to': "N/A" if not hasattr(license, 'uploaded_license_to') else license.uploaded_license_to,
                    'uploaded_sellers_permit_to': "N/A" if not hasattr(license, 'uploaded_sellers_permit_to') else license.uploaded_sellers_permit_to,
                    'uploaded_w9_to ': "N/A" if not hasattr(license, 'uploaded_w9_to ') else license.uploaded_w9_to,
                    'associated_program': "N/A" if not hasattr(license, 'associated_program') else license.associated_program,
                    'profile_category': "N/A" if not hasattr(license, 'profile_category') else license.profile_category
                }
            } for license in license_obj]
            group_by_value[value] = license_profile_kpis

        return Response({"kpis": group_by_value})


class ProfileReportViewSet(viewsets.ModelViewSet):
    """
    All Vendor/account profile related report data stored here.
    """
    serializer_class = ProfileReportSerializer
    permission_classes = (IsAuthenticatedBrandPermission,)
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['report_name']
    filterset_fields = ['profile']

    def get_queryset(self):
        """
        Return queryset based on action.
        """
        reports = ProfileReport.objects.filter()
        if self.action == "list":
            reports = reports.select_related('user')
        reports = reports.filter(user=self.request.user)
        return reports

    def create(self, request):
        """
        This endpoint is used to create report
        """
        serializer = ProfileReportSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class SendVerificationView(APIView):
#     """
#     Send Verification link
#     """
#     serializer_class = Serializer
#     permission_classes = (IsAuthenticatedBrandPermission,)
    
#     def post(self, request):
#         """
#         Post method for verification view link.
#         """
#         serializer = SendVerificationSerializer(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             send_verification_link(request.data.get('email'))
#             response = Response({"Verification link sent!"}, status=200)
#         else:
#             response = Response("false", status=400)
#        return response    
