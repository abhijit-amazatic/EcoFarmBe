
"""
All views related to the two factor authorization defined here.
"""
from django.contrib.auth import login
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, )
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from authy.api import AuthyApiClient
from knox.models import AuthToken


from ..conf import settings
from ..models import (
    TwoFactorLoginToken,
)
from ..serializers import (
    UserSerializer,
    LogInSerializer,
    DeviceIdSerializer,
    TwoFactorLoginDevicesSerializer,
    TwoFactorDevicesChallengeSerializer,
    TwoFactorLogInVerificationSerializer,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


def get_user_login_info(user):
    return {
        "user":            UserSerializer(user).data,
        "existing_member": user.existing_member,
        "is_verified":     user.is_verified,
        "is_approved":     user.is_approved,
        "status":          user.status,
    }


class TwoFactoLogInViewSet(GenericViewSet):
    """
    Login View.
    """
    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = LogInSerializer
    queryset = TwoFactorLoginToken.objects.all()
    lookup_field = 'token'
    lookup_url_kwarg = 'login_2fa_token'

    def create(self, request, *args, **kwargs):
        """"
        Post method for login.
        """
        serializer = LogInSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            if not request.user.is_2fa_enabled:
                response_data = get_user_login_info(request.user)
                response_data["token"] = AuthToken.objects.create(request.user)
            else:
                response_data = {
                    "user": UserSerializer(request.user).data,
                }
                login_2fa_token = TwoFactorLoginToken.objects.create(
                    user=request.user)
                response_data["login_2fa_token"] = login_2fa_token.token

            response = Response(response_data)
        else:
            response = Response({"data": serializer.errors})
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        resp_data = {
            'login_2fa_token': instance.token,
            'is_valid': instance.is_valid,
        }
        return Response(resp_data)

    @action(
        detail=True,
        methods=['get'],
        name='Log In Devices',
        url_name='login-devices',
        url_path='get-devices',
        serializer_class=TwoFactorLoginDevicesSerializer,
    )
    def log_in_devices(self, request, *args, **kwargs):
        """
        Post method view.
        """
        login_2fa_token = self.get_object()
        if login_2fa_token.is_valid:
            serializer = self.serializer_class(
                login_2fa_token.user.get_two_factor_devices(),
                many=True,
            )
            response = Response(serializer.data, status=200)
        else:
            response = Response(
                {"data": "login_2fa_token expired."}, status=401)
        return response

    @action(
        detail=True,
        methods=['post'],
        name='Challenge Log In Device',
        url_name='challenge-login-device',
        url_path='challenge-device',
        serializer_class=TwoFactorDevicesChallengeSerializer,
    )
    def challenge_log_in_device(self, request, *args, **kwargs):
        """
        Post method view.
        """
        login_2fa_token = self.get_object()
        if login_2fa_token.is_valid:
            login(request, login_2fa_token.user)
            serializer_context = self.get_serializer_context()
            serializer = self.serializer_class(
                data=request.data,
                context=serializer_context,
            )
            serializer.is_valid(raise_exception=True)
            device = serializer.device
            if device.is_interactive:
                method = None
                if 'challenge_method' in serializer.validated_data:
                    method = serializer.validated_data['challenge_method']

                device_message = {
                    'phone': 'Your two-factor Login code for Thrive Society is XXXX.',
                    'one_touch': 'Verify your Thrive Society account login.'
                }
                params = {
                    'msg': device_message.get(device.type),
                    'event_code': f'login_{login_2fa_token.token}',
                }
                if method:
                    params['method'] = method
                challenge_status, challenge_data = device.generate_challenge(**params)
                if challenge_status:
                    if device.type in ['one_touch',]:
                        request_id = challenge_data.pop('request_id')
                        login_2fa_token.devices_last_request[device.device_id] = request_id
                        login_2fa_token.save()
                    response = Response(challenge_data, status=200)
                else:
                    response = Response(challenge_data, status=400)
            else:
                response = Response({'detail': "Device in not interactive"}, status=400)
        else:
            response = Response(
                {"detail": "login_2fa_token expired."}, status=401)
        return response

    @action(
        detail=True,
        methods=['post'],
        name='One Touch Log In status',
        url_name='one-touch-log-in-status',
        url_path='one-touch-status',
        serializer_class=DeviceIdSerializer,
    )
    def one_touch_log_in_status(self, request, *args, **kwargs):
        """
        Action.
        """
        login_2fa_token = self.get_object()
        if login_2fa_token.is_valid:
            login(request, login_2fa_token.user)
            serializer_context = self.get_serializer_context()
            serializer = self.serializer_class(
                data=request.data,
                context=serializer_context,
            )
            serializer.is_valid(raise_exception=True)
            device = serializer.device
            if device.type in ['one_touch',]:
                request_id = login_2fa_token.devices_last_request.get(device.device_id, '')
                if request_id:
                    response = Response({'status': device.request_status(request_id)}, status=200)
                else:
                    response = Response({'detail': 'device request not fount'}, status=404)
            else:
                response = Response({"detail": "device is not one_touch device."}, status=400)
        else:
            response = Response({"detail": "login_2fa_token expired."}, status=401)
        return response

    @action(
        detail=True,
        methods=['post'],
        name='Log In verify',
        url_name='login-verify',
        url_path='verify',
        serializer_class=TwoFactorLogInVerificationSerializer,
    )
    def two_factor_log_in_verification(self, request, *args, **kwargs):
        """
        Action.
        """
        login_2fa_token = self.get_object()
        if login_2fa_token.is_valid:
            login(request, login_2fa_token.user)
            serializer_context = self.get_serializer_context()
            serializer = self.serializer_class(
                data=request.data,
                context=serializer_context,
            )
            # setattr(serializer, 'user', login_2fa_token.user)
            serializer.is_valid(raise_exception=True)
            event_code = f'login_{login_2fa_token.token}'
            device = serializer.device
            if device.type in ['one_touch',]:
                token = login_2fa_token.devices_last_request.get(device.device_id, '')
            else:
                token = serializer.validated_data['token']

            if device.verify_token(token=token, event_code=event_code):
                response_data = get_user_login_info(request.user)
                response_data["token"] = AuthToken.objects.create(request.user)
                response = Response(response_data)
            else:
                response = Response({"Device verification failed"}, status=400)
        else:
            response = Response({"detail": "login_2fa_token expired."}, status=401)
        return response
