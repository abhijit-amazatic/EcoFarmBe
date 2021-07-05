# pylint:disable = all
"""
This module defines API views.
"""

import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import serializers
from rest_framework import (permissions, viewsets, status, filters, mixins)
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (AllowAny, IsAuthenticated, )

from .models import (
    BinderLicense,
)
from .serializers import (
    BinderLicenseSerializer,
)

from .utils import (sync_binder_license,)

Auth_User = get_user_model()



class BinderLicenseViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Invite User view
    """
    queryset=BinderLicense.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = BinderLicenseSerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = None

    @action(
        detail=False,
        methods=['put', 'delete'],
        name='Binder License Sync',
        url_name='binder-license-sync',
        url_path='sync',
        permission_classes = (IsAuthenticated, ),
        serializer_class=None,
        authentication_classes = (TokenAuthentication, )
    )
    def license_sync(self, request, *args, **kwargs):
        if request.method.lower() == 'put':
            if sync_binder_license(request.data):
                return Response(status=status.HTTP_202_ACCEPTED)
        elif request.method.lower() == 'delete':
            zoho_crm_id = request.query_params.get('record_id', None)
            if zoho_crm_id:
                try:
                    BinderLicense.objects.get(zoho_crm_id=zoho_crm_id).delete()
                except BinderLicense.DoesNotExist:
                    pass
                else:
                    return Response({'status': 'success'}, status=status.HTTP_200_OK)

        return Response({}, status=status.HTTP_400_BAD_REQUEST)
