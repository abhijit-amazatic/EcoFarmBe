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
from core.utility import (get_license_from_crm_insert_to_db,notify_admins_on_slack,email_admins_on_profile_progress, )
from core.mailer import (mail, mail_send,)
from integration.crm import (get_licenses, update_program_selection, create_records, search_query, update_records)
from user.serializers import (get_encrypted_data,)
from user.views import (notify_admins,)
from permission.filterqueryset import (filterQuerySet, )
from permission.models import Permission
from .models import (
    BinderLicense,
)
from .serializers import (
    BinderLicenseSerializer,
)

from utils import (reverse_admin_change_path,)

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


class BinderLicenseView( APIView):
    """
    All KPI view set
    """
    permission_classes = (IsAuthenticatedBrandPermission, )

    def get(self, request, *args, **kwargs):
        """
        Return QuerySet.
        """
        qs = License.objects.all()
        value_list = qs.values_list('profile_category', flat=True).distinct()
        group_by_value = {}
        for value in value_list:
            license_obj = qs.filter(profile_category=value).select_related()
            license_profile_kpis = []
            for license in license_obj:
                license_data = LicenseSerializer(license).data
                license_profile_kpis.append({
                    'id': license.id,
                    'status': "N/A" if not hasattr(license, 'status') else license.status,
                    'step': "N/A" if not hasattr(license, 'status') else license.step,
                    'updated_on': "N/A" if not hasattr(license, 'updated_on') else license.updated_on,
                    'created_on': "N/A" if not hasattr(license, 'created_on') else license.created_on,
                    'license_type': "N/A" if not hasattr(license, 'license_type') else license.license_type,
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
                    'profile_category': "N/A" if not hasattr(license, 'profile_category') else license.profile_category,
                    'license_url': license_data.get('license_url'),
                    'seller_permit_url': license_data.get('seller_permit_url'),
                    'license_profile_url': license_data.get('license_profile_url'),
                })
            group_by_value[value] = license_profile_kpis

        return Response({"kpis": group_by_value})


class BinderLicenseViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Invite User view
    """
    queryset=BinderLicense.objects.all()
    permission_classes = (IsAuthenticatedBrandPermission, )
    serializer_class = BinderLicenseSerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = None

    # def perform_create(self, serializer):
    #     instance = serializer.save()
    #     send_async_invitation.delay(instance.id)

