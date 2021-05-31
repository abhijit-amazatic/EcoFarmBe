import json
import re
import traceback
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission as DjangoPermission
from django.db import (transaction, DatabaseError) 
from django.db.models import Q
from django.forms.models import model_to_dict
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import serializers
from rest_framework import (permissions, viewsets, status, filters, mixins)
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.decorators import action
from rest_framework.exceptions import (NotFound, PermissionDenied,)
from rest_framework.generics import (GenericAPIView, CreateAPIView,)
from rest_framework.views import APIView
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response


from core.permissions import IsAuthenticatedBrandPermission
from permission.filterqueryset import (filterQuerySet, )
from permission.models import Permission
from compliance_binder.models import BinderLicense
from brand.models import (
    OrganizationUser,
    OrganizationUserRole,
    OrganizationUserInvite,
)
from .models import (
    InternalOnboardingInvite,
)
from .serializers import (
    InternalOnboardingSerializer,
    InternalOnboardingInviteVerifySerializer,
    InternalOnboardingInviteSetPassSerializer,
)


class InternalOnboardingView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    User Invitation Verification View.
    """
    permission_classes = (AllowAny, )
    serializer_class = InternalOnboardingSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                pass
        except DatabaseError as exc:
            return Response({'detail': f'Error: {exc}'}, status=400)



    @action(
        detail=False,
        methods=['post'],
        name='Invite Verify',
        url_name='internal-onboarding-invite-verify',
        url_path='invite-verify',
        permission_classes=(AllowAny,),
        serializer_class=InternalOnboardingInviteVerifySerializer
    )
    def invite_verify(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,)
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['token']
        user = instance.user
        response_data = {
            'new_user': True if not user.last_login else False,
            'is_password_set': user.has_usable_password(),
            'email': user.email,
            'full_name': user.get_full_name(),
        }
        if instance.status in ('pending',):
            organization_user, _ = OrganizationUser.objects.get_or_create(
                organization=instance.organization,
                user=user,
            )

            for role in instance.roles.all():
                organization_user_role, _ = OrganizationUserRole.objects.get_or_create(
                    organization_user=organization_user,
                    role=role,
                )
                organization_user_role.licenses.add(instance.license)
                instance.completed_on = timezone.now()
            instance.status = 'completed'
            instance.save()
            response_data['detail'] = 'Accepted'
            response = Response(response_data, status=status.HTTP_200_OK)
        elif instance.status == 'completed':
            response = Response({'detail': 'Already accepted'},status=200)
        else:
            response = Response({'detail': 'invalid token'},status=400)
        return response

    @action(
        detail=False,
        methods=['post'],
        name='Set Password',
        url_name='internal-onboarding-invite-set-pass',
        url_path='invite-set-password',
        permission_classes=(AllowAny,),
        serializer_class=InternalOnboardingInviteSetPassSerializer,
    )
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,)
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['token']
        user = instance.user
        if instance.status == 'completed':
            if not user.last_login and not user.has_usable_password():
                user.set_password(serializer.validated_data['new_password'])
                response = Response({'detail': 'Password set successfull'}, status=200)
            else:
                response = Response({'detail': 'Already have a password for this account'}, status=400)
        else:
            response = Response({'detail': 'Invite is not completed'}, status=400)
        return response