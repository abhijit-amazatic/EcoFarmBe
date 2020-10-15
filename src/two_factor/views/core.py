
"""
All views related to the two factor authorization defined here.
"""
from rest_framework.permissions import (IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from authy.api import AuthyApiClient

from user.models import (PrimaryPhoneTOTPDevice,)

from ..conf import settings
from ..models import (
    StaticDevice,
)
from ..serializers import (
    CurrentPasswordSerializer,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


class TwoFactorLoginEnableView(GenericAPIView):
    """
    View
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CurrentPasswordSerializer

    def post(self, request, *args, **kwargs):
        """
        Post method view.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        PrimaryPhoneTOTPDevice.objects.get_or_create(user=user)
        if not user.is_2fa_enabled:
            if user.get_two_factor_devices():
                StaticDevice.objects.filter(user=user).delete()
                static_device = StaticDevice.objects.create(user=user)
                static_tokens = static_device.genrate_tokens()
                user.is_2fa_enabled = True
                user.save()
                response = Response(
                    {
                        'detail': 'Two factor login is enabled.',
                        'backup_tokens': static_tokens,
                    },
                    status=200
                )
            else:
                response = Response(
                    {'detail': 'Require at least on verified device.'}, status=400)
        else:
            response = Response(
                {'detail': 'Two factor login is already enabled.'}, status=400)
        return response


class TwoFactorLoginDisableView(GenericAPIView):
    """
    View
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CurrentPasswordSerializer

    def post(self, request, *args, **kwargs):
        """
        Post method view.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        if user.is_2fa_enabled:
            StaticDevice.objects.filter(user=user).delete()
            user.is_2fa_enabled = False
            user.save()
            response = Response(
                {'detail': 'Two factor login is disabled.'}, status=200)
        else:
            response = Response(
                {'detail': 'Two factor login is already disabled.'}, status=400)
        return response
