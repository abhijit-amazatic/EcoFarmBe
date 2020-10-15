
"""
All views related to the two factor authorization defined here.
"""
import qrcode
import qrcode.image.svg
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated, )
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.settings import api_settings
from authy.api import AuthyApiClient

from ..conf import settings
from ..models import (
    AuthyUser,
    AuthyAddUserRequest,
    AuthyOneTouchDevice,
    PhoneTOTPDevice,
)
from ..serializers import (
    AddPhoneDeviceSerializer,
    TwoFactorDevicesSerializer,
    EmptySerializer,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


class AddPhoneDeviceViewSet(GenericViewSet):
    """
    View
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = AddPhoneDeviceSerializer
    queryset = AuthyAddUserRequest.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = PhoneTOTPDevice.objects.create(
            user=self.request.user,
            phone_number=serializer.validated_data['phone_number']
        )
        device_serializer = TwoFactorDevicesSerializer(instance)
        return Response(device_serializer.data, status=201)
