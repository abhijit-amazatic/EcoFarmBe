
"""
All views related to the two factor authorization defined here.
"""
from django.contrib.auth import login
from django.http import (
    Http404,
)
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated, )
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from authy.api import AuthyApiClient
from knox.models import AuthToken

from user.models import PrimaryPhoneTOTPDevice
from ..conf import settings
from ..models import (
    TwoFactorLoginToken,
    StaticDevice,
)
from ..serializers import (
    UserSerializer,
    LogInSerializer,
    DeviceIdSerializer,
    TwoFactorDevicesSerializer,
    TwoFactorDevicesChallengeMethodSerializer,
    TokenSerializer,
    TwoFactorLogInVerificationSerializer,
    EmptySerializer,
    CurrentPasswordSerializer,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)



class TwoFactorDeviceViewSet(mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin,
                                 GenericViewSet):
    """
    Login View.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = TwoFactorDevicesSerializer
    lookup_field = 'device_id'
    lookup_url_kwarg = 'device_id'


    def  get_queryset(self):
        return self.request.user.get_two_factor_devices(confirmed_only=False)

    def get_object(self):
        """
        Returns the object the view is displaying.
        """
        queryset = self.get_queryset()

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s".' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        queryset = [
            x
            for x in queryset if getattr(x, self.lookup_field) == self.kwargs[lookup_url_kwarg]
        ]

        if not queryset:
            raise Http404('Device not found.')
        obj = queryset[0]

        self.check_object_permissions(self.request, obj)
        return obj

    @action(
        detail=True,
        methods=['post'],
        name='Challenge Device Verification',
        url_name='challenge-device-verification',
        url_path='challenge-device-verification',
        serializer_class=TwoFactorDevicesChallengeMethodSerializer,
    )
    def challenge_log_in_device(self, request, *args, **kwargs):
        """
        Post method view.
        """
        device = self.get_object()
        if not device.confirmed:
            serializer = self.get_serializer(device, data=request.data)
            serializer.is_valid(raise_exception=True)
            if device.is_interactive:
                method = None
                if 'challenge_method' in serializer.validated_data:
                    method = serializer.validated_data['challenge_method']

                params = {
                    'event_code': 'device_verification',
                }
                if method:
                    params['method'] = method
                challenge_ok, challenge_data = device.generate_challenge(**params)
                if challenge_ok:
                    if device.type in ['one_touch',]:
                        _ = challenge_data.pop('request_id')
                    response = Response(challenge_data, status=200)
                else:
                    response = Response(challenge_data, status=400)
            else:
                response = Response({'detail': "Device in not interactive"}, status=400)
        else:
            response = Response({'detail': "Device is already verified"}, status=400)
        return response


    @action(
        detail=True,
        methods=['post'],
        name='Verify Device',
        url_name='verify-device',
        url_path='verify',
        serializer_class=TokenSerializer,
    )
    def device_verification(self, request, *args, **kwargs):
        """
        Action.
        """
        device = self.get_object()
        if not device.confirmed:
            serializer = self.get_serializer(device, data=request.data)
            serializer.is_valid(raise_exception=True)
            event_code = 'device_verification'
            token = serializer.validated_data['token']
            if device.verify_token(token=token, event_code=event_code):
                device.confirmed = True
                device.save()
                response = Response({'detail': "Device verification successfull."}, status=200)
            else:
                response = Response({'detail': "Device verification failed"}, status=400)
        else:
            response = Response({'detail': "Device is already verified"}, status=400)
        return response

    @action(
        detail=True,
        methods=['post'],
        name='Remove Device',
        url_name='remove-device',
        url_path='remove',
        serializer_class=CurrentPasswordSerializer,
    )
    def remove(self, request, *args, **kwargs):
        """
        Action.
        """
        device = self.get_object()
        serializer = self.get_serializer(device, data=request.data)
        serializer.is_valid(raise_exception=True)
        if device.is_removable:
            device.delete()
            return Response(status=204)
        return Response({'detail': 'Device is not removeable.'}, status=400)
