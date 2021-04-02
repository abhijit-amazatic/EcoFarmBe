# pylint:disable = all
"""
This module defines API views.
"""

import json
import re
import traceback
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission as DjangoPermission
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import serializers
from rest_framework import (permissions, viewsets, status, filters, mixins)
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.decorators import action
from rest_framework.exceptions import (NotFound, PermissionDenied,)
from rest_framework.generics import (GenericAPIView, CreateAPIView,)
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from rest_framework.permissions import (AllowAny, IsAuthenticated, )

from core.permissions import IsAuthenticatedBrandPermission
from inventory.models import (Documents, )
from integration.books import  get_buyer_summary
from integration.apps.aws import (create_presigned_url, )
from core.utility import (get_license_from_crm_insert_to_db,notify_admins_on_slack,)
from core.mailer import (mail, mail_send,)
from integration.crm import (get_licenses, update_program_selection, create_records, search_query, update_records)
from user.serializers import (get_encrypted_data,)
from user.views import (notify_admins,)
from permission.filterqueryset import (filterQuerySet, )
from .tasks import (
    send_async_invitation,
    send_onboarding_data_fetch_verification,
    resend_onboarding_data_fetch_verification,
)
from permission.models import Permission
from .models import (
    Organization,
    Brand, License,
    # LicenseUser,
    ProfileContact,
    LicenseProfile,
    CultivationOverview,
    CropOverview,
    FinancialOverview,
    ProgramOverview,
    # BillingInformation,
    ProfileCategory,
    ProfileReport,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    # Permission,
    OrganizationUserInvite,
    OnboardingDataFetch,
)
from .serializers import (
    OrganizationSerializer,
    BrandSerializer,
    LicenseSerializer,
    ProfileContactSerializer,
    CultivationOverviewSerializer,
    LicenseProfileSerializer,
    FinancialOverviewSerializer,
    CropOverviewSerializer,
    ProgramOverviewSerializer,
    BillingInformationSerializer,
    ProfileReportSerializer,
    FileUploadSerializer,
    InviteUserSerializer,
    CurrentPasswordSerializer,
    OrganizationRoleSerializer,
    OrganizationUserNestedViewSerializer,
    OrganizationUserRoleNestedSerializer,
    # PermissionSerializer,
    OrganizationDetailSerializer,
    InviteUserVerificationSerializer,
    OTPSerializer,
    OnboardingDataFetchSerializer,
    MyOrganizationRoleSerializer,
)
from .views_mixin import (
    NestedViewSetMixin,
    PermissionQuerysetFilterMixin,
)
from .views_permissions import (
    LicenseViewSetPermission,
    OrganizationViewSetPermission,
    BrandViewSetPermission,
    OrganizationRoleViewSetPermission,
    OrganizationUserViewSetPermission,
    OrganizationUserRoleViewSetPermission,
)

Auth_User = get_user_model()



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


class OrganizationViewSet(PermissionQuerysetFilterMixin,
                                    viewsets.ModelViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedBrandPermission, OrganizationViewSetPermission, )
    queryset = Organization.objects.all()
    serializer_class = OrganizationDetailSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'created_by']

    def get_queryset(self):
        """
        Return queryset based on action.
        """
        qs = super().get_queryset()
        qs.select_related('roles', 'licenses')
        return qs

    def get_serializer_class(self):
        """
        Return serializer on the basis of action.
        """
        if self.action == 'destroy':
            return CurrentPasswordSerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        obj = serializer.save()
        result = search_query('Orgs', obj.__dict__['name'], 'Name')
        if result.get('status_code') == 200:
            organization_id = result.get('response')[0].get('id')
            result = update_records('Orgs', obj.__dict__, True)
        else:
            try:
                result = create_records('Orgs', obj.__dict__)
            except Exception as exc:
                    print('Error while creating Organization in Zoho CRM')
                    print(exc)
            if result.get('status_code') in [200, 201]:
                try:
                    organization_id = result['response'][0]['id']
                except KeyError:
                    organization_id = result['response']['response']['data'][0]['details']['id']
                if organization_id:
                    obj.zoho_crm_id = organization_id
                    obj.save()
                else:
                    print('Error while Extrating zoho_crm_id for created Organization in Zoho CRM')
                    print(result)
            else:
                print('Error while creating Organization in Zoho CRM')
                print(result)


class BrandViewSet(PermissionQuerysetFilterMixin,
                    NestedViewSetMixin, viewsets.ModelViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedBrandPermission, BrandViewSetPermission, )
    queryset = Brand.objects.get_queryset()
    filter_backends = [filters.SearchFilter]
    serializer_class =BrandSerializer
    search_fields = ['brand_name', ]


class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):
    owner_or_manager__in = CharInFilter(field_name='owner_or_manager', lookup_expr='in')
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    premises_county__in = CharInFilter(field_name='premises_county', lookup_expr='in')
    license_type__in = CharInFilter(field_name='license_type', lookup_expr='in')

    class Meta:
        model = License
        fields = {
            'profile_category':['icontains', 'exact'],
            'legal_business_name':['icontains', 'exact'],
            'owner_or_manager__in':['icontains', 'exact'],
            'status__in':['icontains', 'exact'],
            'license_type__in':['icontains', 'exact'],
            'premises_county__in':['icontains', 'exact']
        }

class LicenseViewSet(PermissionQuerysetFilterMixin,
                        NestedViewSetMixin, viewsets.ModelViewSet):
    """
    All LicenseViewSet
    """
    permission_classes = (IsAuthenticatedBrandPermission, LicenseViewSetPermission, )
    queryset = License.objects.get_queryset()
    profile_contact_path = 'profile-contact(/(?P<profile_contact_id>[0-9]*))?'
    cultivation_overview_path = 'cultivation-overview(/(?P<cultivation_overview_id>[0-9]*))?'
    license_profile_path = 'license-profile(/(?P<license_profile_id>[0-9]*))?'
    financial_overview_path = 'financial-overview(/(?P<financial_overview_id>[0-9]*))?'
    crop_overview_path = 'crop-overview(/(?P<crop_overview_id>[0-9]*))?'
    program_overview_path = 'program-overview(/(?P<program_overview_id>[0-9]*))?'
    billing_information_path = 'billing_information(/(?P<billing_information_id>[0-9]*))?'
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    search_fields = ['status', 'profile_category']
    filterset_fields = ['profile_category', 'legal_business_name']
    filterset_class = DataFilter

    action_select_related_fields_map = {
        'list':                 ('brand',),
        'profile_contact':      ('profile_contact',),
        'cultivation_overview': ('cultivation_overview',),
        'license_profile':      ('license_profile',),
        'financial_overview':   ('financial_overview',),
        'crop_overview':        ('crop_overview',),
        'program_overview':     ('program_overview',),
    }

    def get_queryset(self):
        """
        Return queryset.
        """
        qs = super().get_queryset()
        select_related_fields = self.action_select_related_fields_map.get(self.action)
        if select_related_fields:
            qs = qs.select_related(*select_related_fields)
        return qs

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
        elif self.action == 'billing_information':
            return BillingInformationSerializer
        return LicenseSerializer

    def perform_create(self, serializer):
        """
        This is used to create License.
        """
        instance = serializer.save()
        try:
            user = instance.organization.created_by
            notify_admins_on_slack(user.email,instance)
            # if user.existing_member:
            #     existing_user_license_nos = get_license_numbers(user.legal_business_name)
            #     if instance.license_number in existing_user_license_nos:
            #         get_license_from_crm_insert_to_db(user.id,instance.license_number,instance.id)
            #     elif instance.license_number not in existing_user_license_nos:
            #         instance.is_data_fetching_complete = True
            #         instance.save()
            #     pass
        except Exception as e:
            print('Exception while creating & pulling existing user license',e)
            traceback.print_tb(e.__traceback__)

    def extra_info(self, request, pk, model, serializer, extra_info_attribute):
        """
        Generic feature for detail route.
        """
        license = self.get_object()
        if request.method == 'GET':
            try:
                instance = getattr(license, extra_info_attribute)
                data = serializer(instance).data
                if extra_info_attribute == 'profile_contact':
                    data = self.add_user_profile_image_to_cantacts(data)
            except model.DoesNotExist:
                return Response({})
            else:
                return Response(data)

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

    def add_user_profile_image_to_cantacts(self, data):
        employees =  data.get('profile_contact_details', {}).get('employees')
        profile_images_dict = {}
        if employees and isinstance(employees, list):
            for employee in employees:
                if isinstance(employee, dict):
                    document_url = None
                    if employee.get('employee_email'):
                        email = employee.get('employee_email', '')
                        if email in profile_images_dict:
                            document_url = profile_images_dict.get(email)
                        else:
                            try:
                                user = Auth_User.objects.get(email=email)
                            except Auth_User.DoesNotExist:
                                pass
                            else:
                                try:
                                    document = Documents.objects.filter(object_id=user.id, doc_type='profile_image').latest('created_on')
                                    if document.box_url:
                                        document_url = document.box_url
                                    else:
                                        path = document.path
                                        url = create_presigned_url(settings.AWS_BUCKET, path)
                                        if url.get('response'):
                                            document_url = url.get('response')
                                except Exception:
                                    pass
                            profile_images_dict[email] = document_url
                    employee['document_url'] = document_url
        return data

    @action(detail=True, url_path='existing-user-data-status', methods=['get'])
    def existing_user_data_status(self, request, pk, *args, **kwargs):
        """
        existing user data status
        """
        license_obj = self.get_object()
        return Response({"is_data_fetching_complete":license_obj.is_data_fetching_complete})

    @action(detail=True, url_path=profile_contact_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def profile_contact(self, request, pk, profile_contact_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on profile_contact.
        """
        return self.extra_info(request, pk, ProfileContact, ProfileContactSerializer, 'profile_contact')

    @action(detail=True, url_path=cultivation_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def cultivation_overview(self, request, pk, cultivation_overview_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on cultivation_overview.
        """
        return self.extra_info(request, pk, CultivationOverview, CultivationOverviewSerializer, 'cultivation_overview')

    @action(detail=True, url_path=financial_overview_path, methods=['get', 'delete', 'patch'], pagination_class=CustomPagination)
    def financial_overview(self, request, pk, financial_overview_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on financial_overview.
        """
        return self.extra_info(request, pk, FinancialOverview, FinancialOverviewSerializer, 'financial_overview')

    @action(detail=True, url_path=crop_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def crop_overview(self, request, pk, crop_overview_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on crop_overview.
        """
        return self.extra_info(request, pk, CropOverview, CropOverviewSerializer, 'crop_overview')

    @action(detail=True, url_path=program_overview_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def program_overview(self, request, pk, program_overview_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on program_overview.
        """
        return self.extra_info(request, pk, ProgramOverview, ProgramOverviewSerializer, 'program_overview')

    @action(
        detail=True,
        url_path=billing_information_path,
        methods=['get', 'patch'],
        pagination_class=CustomPagination,
    )
    def billing_information(self, request, pk, program_overview_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on billing_information.
        """
        return self.extra_info(request, pk, LicenseProfile, BillingInformationSerializer, 'license_profile')

    @action(detail=True, url_path=license_profile_path, methods=['get', 'patch'], pagination_class=CustomPagination)
    def license_profile(self, request, pk, license_profile_id=None, *args, **kwargs):
        """
        Detail route CRUD operations on license_profile.
        """
        return self.extra_info(request, pk, LicenseProfile, LicenseProfileSerializer, 'license_profile')

    @action(detail=True, url_path='buyer-summary', methods=['get'])
    def buyer_summary(self, request, pk, *args, **kwargs):
        """
        get buyer summary
        """
        license_obj = self.get_object()
        if license_obj.is_buyer:
            return Response({'buyer_summary':get_buyer_summary(license_obj.legal_business_name)},status=200)
        else:
            return Response({'detail':"License is not asscoaited with buyer account or couldn't fetch summary!"}, status=400)



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


class KpiViewSet(NestedViewSetMixin, APIView):
    """
    All KPI view set
    """
    permission_classes = (IsAuthenticatedBrandPermission, )

    def get(self, request, *args, **kwargs):
        """
        Return QuerySet.
        """
        qs = License.objects.all()
        qs = self.filter_queryset_by_parents_lookups(qs)
        qs = filterQuerySet.for_user(qs, request.user)
        value_list = qs.values_list('profile_category', flat=True).distinct()
        group_by_value = {}
        for value in value_list:
            license_obj = qs.filter(profile_category=value).select_related()
            #license_profile_kpis = license_obj.values()
            license_profile_kpis = []
            for license in license_obj:
                if hasattr(license, 'brand'):
                    brand_data = BrandSerializer(license.brand).data
                else:
                    brand_data = {}
                license_data = LicenseSerializer(license).data
                license_profile_kpis.append({
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
                    'program_name': '' if not hasattr(license, 'program_overview') else license.program_overview.program_details.get('program_name', ''),
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
                        'document_url': brand_data.get('document_url'),
                        'brand_image': brand_data.get('brand_image'),
                        
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
                        'profile_category': "N/A" if not hasattr(license, 'profile_category') else license.profile_category,
                        'license_url': license_data.get('license_url'),
                        'seller_permit_url': license_data.get('seller_permit_url'),
                        'license_profile_url': license_data.get('license_profile_url'),
                    }
                })
            group_by_value[value] = license_profile_kpis

        return Response({"kpis": group_by_value})


class OrganizationRoleViewSet(PermissionQuerysetFilterMixin,
                                NestedViewSetMixin, viewsets.ModelViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedBrandPermission, OrganizationRoleViewSetPermission, )
    queryset = OrganizationRole.objects.get_queryset()
    filter_backends = [filters.SearchFilter]
    serializer_class = OrganizationRoleSerializer
    search_fields = ['name', ]

class OrganizationUserViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticatedBrandPermission, OrganizationUserViewSetPermission, )
    queryset = OrganizationUser.objects.get_queryset()
    filter_backends = [filters.SearchFilter]
    serializer_class = OrganizationUserNestedViewSerializer
    search_fields = ['user__email', ]

class OrganizationUserRoleViewSet(PermissionQuerysetFilterMixin,
                                NestedViewSetMixin, viewsets.ModelViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticated, OrganizationUserRoleViewSetPermission, )
    queryset = OrganizationUserRole.objects.get_queryset()
    filter_backends = [filters.SearchFilter]
    serializer_class = OrganizationUserRoleNestedSerializer
    search_fields = ['organization_user__user__email', 'role__name']

    def get_queryset(self):
        """
        Return queryset based on action.
        """
        qs = super(viewsets.ModelViewSet, self).get_queryset()
        qs = qs.filter(
            organization_user__organization=self.context_parent['organization'])
        return  qs


class MyOrganizationRoleView(APIView):
    """
    All KPI view set
    """
    permission_classes = (IsAuthenticatedBrandPermission, )

    def get(self, request, *args, **kwargs):
        """
        Return QuerySet.
        """
        parents_query_dict = self.get_parents_query_dict()
        org_id = parents_query_dict.get('organization')
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response([])
        else:
            data = {}
            if org.created_by_id == request.user.id:
                data["role_info"] = {
                        "name": "Org Admin",
                        "permissions": Permission.objects.filter(type='organizational').values_list('id', flat=True).distinct(),
                    }
                data["licenses"] = License.objects.filter(organization=org).values_list('id', flat=True).distinct()

            qs = OrganizationUserRole.objects.filter(
                organization_user__organization_id=org)
            qs = qs.filter(organization_user__user=request.user)
            serializers = MyOrganizationRoleSerializer(
                qs,
                context={
                    'view': self,
                    'request': request,
                    'format': self.kwargs,
                },
                many=True,
            )
            resp_data = serializers.data
            if data:
                resp_data.append(data)
            return Response(resp_data)

    def get_parents_query_dict(self, **kwargs):
        result = {}
        for kwarg_name, kwarg_value in self.kwargs.items():
            if kwarg_name.startswith('parent_'):
                query_lookup = kwarg_name.replace(
                    'parent_',
                    '',
                    1
                )
                result[query_lookup] = kwarg_value
        return result

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

class InvitesDataFilter(FilterSet):
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    class Meta:
        model = OrganizationUserInvite
        fields = {
            'status':['icontains', 'exact'],
        }


class InviteUserViewSet(NestedViewSetMixin,
                        mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """
    Invite User view
    """
    queryset=OrganizationUserInvite.objects.all()
    permission_classes = (IsAuthenticatedBrandPermission, )
    serializer_class = InviteUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status',]
    filterset_class = InvitesDataFilter

    def perform_create(self, serializer):
        instance = serializer.save()
        send_async_invitation.delay(instance.id)

    @action(
        detail=True,
        methods=['post'],
        name='Resend Invitation',
        url_name='resend-invitation',
        url_path='resend',
        serializer_class=serializers.Serializer,
    )
    def resend_invitation(self, request, pk, *args, **kwargs):
        """
        Resend Invitation
        """
        instance = self.get_object()
        send_async_invitation.delay(instance.id)
        return Response(status=200)

class UserInvitationVerificationView(GenericAPIView):
    """
    User Invitation Verification View.
    """
    permission_classes = (AllowAny, )
    serializer_class = InviteUserVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['token']
        if instance.status in ['pending', 'user_joining_platform']:
            instance.is_invite_accepted = True
            response_data = {
                'new_user': True,
                'email': instance.email,
                'full_name': instance.full_name,
            }
            try:
                user = Auth_User.objects.get(email=instance.email)
            except Auth_User.DoesNotExist:
                instance.status = 'user_joining_platform'
            else:
                response_data['new_user'] = False
                organization_user, _ = OrganizationUser.objects.get_or_create(
                    organization=instance.organization,
                    user=user,
                )
                organization_user_role, _ = OrganizationUserRole.objects.get_or_create(
                    organization_user=organization_user,
                    role=instance.role,
                )
                organization_user_role.licenses.add(*instance.licenses.all())

                instance.status = 'completed'
            response = Response(response_data, status=status.HTTP_200_OK)
        elif instance.status == 'completed':
            response = Response(
                {'detail': 'Already accepted'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            response = Response(
                {'detail': 'invalid token'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.save()
        return response


class LicenseSyncView(APIView):
    """
    Sync licenses from crm to db.
    """
    authentication_classes = (TokenAuthentication, )

    def put(self, request):
        """
        Update license.
        """
        license_number = request.data.get('license_number')
        issue = request.data.get('issue')
        expiry = request.data.get('expiry')
        record_id = request.data.get('account_id')
        owner_id = request.data.get('owner_id')
        owner_email = request.data.get('owner_email')
        if license_number and expiry:
            try:
                license_obj = License.objects.get(license_number=license_number)
                date_time_obj = datetime.datetime.strptime(expiry, '%Y-%m-%d')
                license_obj.expiration_date = date_time_obj.date()
                license_obj.is_updated_via_trigger = True
                license_obj.issue_date = issue
                license_obj.save()
                if license_obj.expiration_date >= timezone.now().date():
                    if license_obj.status_before_expiry:
                        license_obj.status = license_obj.status_before_expiry
                        license_obj.save()
                    else:
                        license_obj.status = 'completed'
                        license_obj.save()
                return Response(status=status.HTTP_202_ACCEPTED)
            except License.DoesNotExist:
                pass
        elif record_id and owner_id and owner_email:
            record = LicenseProfile.objects.get(zoho_crm_id=record_id)
            record.crm_owner_id = owner_id
            record.crm_owner_email = owner_email
            record.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ProgramSelectionSyncView(APIView):
    """
    Sync program selection from crm to db.
    """
    authentication_classes = (TokenAuthentication, )

    def put(self, request):
        """
        Update program selection.
        """
        record_id = request.data.get('record_id')
        tier_selection = request.data.get('tier_selection')
        response = update_program_selection(record_id, tier_selection)
        if response['code'] == 0:
            return Response(response)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

class OnboardingDataFetchViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                                                        viewsets.GenericViewSet):
    """
    All Brand related endpoint's view is defined here.
    """
    permission_classes = (IsAuthenticated,)
    queryset = OnboardingDataFetch.objects.get_queryset()
    filter_backends = [filters.SearchFilter]
    serializer_class = OnboardingDataFetchSerializer
    lookup_field = 'data_fetch_token'


    def get_serializer_class(self):
        if self.action == 'retrive':
            return 
        else:
            return super().get_serializer_class()

    def perform_create(self, serializer):
        """
        This is used to create License.
        """
        instance = serializer.save()
        try:
            send_onboarding_data_fetch_verification.delay(instance.id, self.request.user.id)
        except Exception as e:
            print('Exception while creating & pulling existing user license',e)
            traceback.print_tb(e.__traceback__)

    @action(
        detail=True,
        methods=['post'],
        name='Otp Verification',
        url_name='verify-datafetch-otp',
        url_path='verify-otp',
        serializer_class=OTPSerializer,
    )
    def verify_otp(self, request, *args, **kwargs):
        """
        Verify License Datafetch Otp
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        if instance.owner_verification_status == 'verification_code_sent':
            if instance.verify_otp(serializer.validated_data['otp']):
                instance.owner_verification_status = 'verified'
                instance.save()
                return Response({}, status=status.HTTP_200_OK,)
            else:
                return Response({"otp": "Invalid OTP,"}, status=400)
        else:
            return Response({"detail": "Invalid step,"}, status=400)

    @action(
        detail=True,
        methods=['post'],
        name='Resend Verification',
        url_name='resend-otp',
        url_path='resend-otp',
        serializer_class=serializers.Serializer,
    )
    def resend_otp(self, request, *args, **kwargs):
        """
        Verify License Datafetch Otp
        """
        instance = self.get_object()
        resend_onboarding_data_fetch_verification.delay(instance.id, self.request.user.id)
        return Response({}, status=status.HTTP_200_OK,)
