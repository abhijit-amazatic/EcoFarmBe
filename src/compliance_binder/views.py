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

