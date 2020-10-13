
"""
All views related to the two factor authorization defined here.
"""
import qrcode
import qrcode.image.svg
import json
from django.http import HttpResponse
from django.contrib.auth import login
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from authy.api import AuthyApiClient
from knox.models import AuthToken
from knox.settings import knox_settings

from user.models import (PrimaryPhoneTOTPDevice,)

from .conf import settings
from .utils import (
    validate_authy_callback_request_signature
)
from .models import (
    TwoFactorLoginToken,
    AuthyUser,
    AuthyAddUserRequest,
    AuthyOneTouchDevice,
    AuthyOneTouchRequest,
    PhoneTOTPDevice,
    AuthyOneTouchDevice,
    AuthenticatorTOTPDevice,
    StaticDevice,
    StaticToken,
)
from .serializers import (
    LogInSerializer,
    TwoFactorDevicesSerializer,
    DeviceIdSerializer,
    TwoFactorDevicesChallengeSerializer,
    TwoFactorLogInVerificationSerializer,
    AuthyAddUserRequestSerializer,
    EmptySerializer,
    CurrentPasswordSerializer,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)
KNOXUSER_SERIALIZER = knox_settings.USER_SERIALIZER


def get_user_login_info(user):
    return {
        "user":            KNOXUSER_SERIALIZER(user).data,
        "existing_member": user.existing_member,
        "is_2fa_enabled":  user.is_2fa_enabled,
        "is_verified":     user.is_verified,
        "is_approved":     user.is_approved,
        "status":          user.status,
    }


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
                    "user": KNOXUSER_SERIALIZER(request.user).data,
                    "is_2fa_enabled":  request.user.is_2fa_enabled,
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
        serializer_class=TwoFactorDevicesSerializer,
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
        methods=['get'],
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
                response = Response({"detail": "Device verification failed"}, status=400)
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


class AuthyAddUserRequestViewSet(mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin,
                                 GenericViewSet):
    """
    View
    """
    serializer_class = AuthyAddUserRequestSerializer
    permission_classes = (IsAuthenticated,)
    queryset = AuthyAddUserRequest.objects.all()
    lookup_field = 'request_id'
    lookup_url_kwarg = 'request_id'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    @action(
        detail=False,
        methods=['post'],
        name='Add Default User',
        url_name='authy-user-registration-default',
        url_path='add-default-user',
        serializer_class=EmptySerializer,
    )
    def add_default_user(self, request, *args, **kwargs):
        """
        Add user using phone_number and email id.
        """
        user = request.user
        if user.phone.is_valid:
            if user.is_phone_verified:
                authy_user = authy_api.users.create(
                    email=user.email,
                    phone=user.phone.national_number,
                    country_code=user.phone.country_code,
                )

                if authy_user.ok():

                    authy_user_instance, _ = AuthyUser.objects.get_or_create(
                        user=user)
                    authy_user_instance.authy_id = authy_user.id or authy_user.content[
                        'user']['id']
                    authy_user_instance.save()
                    AuthyOneTouchDevice.objects.create(user=user)
                    response = Response(
                        {'detail': 'authy User devices process successfully.'}, status=400)

                    response = Response(
                        authy_user.content['message'], status=200)
                else:
                    errors = authy_user.errors()
                    errors['detail'] = errors.pop(
                        'message', 'error while creating user.')
                    response = Response(errors, status=400)

            else:
                response = Response(
                    {"detail": "users phone number is not verified."}, status=400)
        else:
            response = Response(
                {"detail": "users phone number is not valid."}, status=400)
        return response

    @action(
        detail=True,
        methods=['get'],
        name='Get Resitration QRString',
        url_name='authy-user-registration-qrstring',
        url_path='registration-qrstring',
        serializer_class=EmptySerializer,
    )
    def get_qrstring(self, request, *args, **kwargs):
        """
        Create authy user registration QRString.
        """

        instance = self.get_object()
        return Response(instance.get_qr_string(), status=400)

    @action(
        detail=True,
        methods=['get'],
        name='Get Resitration QRCode',
        url_name='authy-user-registration-qrcode',
        url_path='registration-qrcode',
        serializer_class=EmptySerializer,
    )
    def get_resitration_qrcode(self, request, *args, **kwargs):
        """
        Authy user registration QRCode.
        """
        add_user_request = self.get_object()
        image_content_types = {
            'PNG': 'image/png',
            'SVG': 'image/svg+xml; charset=utf-8',
        }
        image_factory = qrcode.image.svg.SvgPathFillImage

        img = qrcode.make(
            add_user_request.get_qr_string(),
            image_factory=image_factory
        )
        resp = HttpResponse(
            content_type=image_content_types[image_factory.kind])
        img.save(resp)
        return resp

    @action(
        detail=True,
        methods=['get'],
        name='Get Registration Status',
        url_name='authy-user-registration-status',
        url_path='registration-status',
        serializer_class=EmptySerializer,
    )
    def registration_status(self, request, *args, **kwargs):
        """
        Get authy user registration status.
        """
        instance = self.get_object()
        authy_user = authy_api.users.registration_status(
            custom_user_id=instance.custom_user_id
        )

        if authy_user.ok():
            # {'registration': {'authy_id': 217244768, 'status': 'completed'}, 'success': True}
            instance.authy_id = authy_user.content['registration']['authy_id']
            instance.is_registered = authy_user.content['registration']['status'] == 'completed'
            instance.save()
            response = Response(authy_user.content, status=200)
        else:
            response = Response(authy_user.content, status=400)
        return response

    @action(
        detail=True,
        methods=['post'],
        name='process authy user registration',
        url_name='authy-add-user-request-process',
        url_path='process',
        serializer_class=EmptySerializer,
    )
    def create_authy_devices(self, request, *args, **kwargs):
        """
        Process authy add user request.
        """
        user = self.request.user
        instance = self.get_object()

        if instance.is_registered:
            authy_user, _ = AuthyUser.objects.get_or_create(
                authy_id=instance.authy_id)
            try:
                device = AuthyOneTouchDevice.objects.get(user=user)
            except AuthyOneTouchDevice.DoesNotExist:
                device = AuthyOneTouchDevice.objects.create(
                    user=user, authy_user=authy_user, confirmed=True)
            else:
                device.authy_user = authy_user
                device.confirmed = True
                device.save()
            response = Response(
                {'detail': 'authy User devices process successfully.'}, status=400)

        else:
            response = Response(
                {'detail': 'authy User registration is not complete.'}, status=400)
        return response


class AuthyOneTouchRequestCallbackView(APIView):
    """
    View
    """
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Post method view.
        """
        if validate_authy_callback_request_signature(request):
            uuid = request.data.get('uuid')
            if uuid:
                instance = AuthyOneTouchRequest.objects.filter(
                    authy_request_uuid=uuid).first()
                if instance:
                    transaction = request.data.get(
                        'approval_request', {}).get('transaction')
                    if transaction:
                        instance.status = request.data.get(
                            'status') or transaction.get('status')
                        event_code = transaction.get(
                            'hidden_details', {}).get('event_code')
                        if event_code:
                            instance.event_code = event_code
                    instance.authy_response = request.data
                    instance.save()
            return Response("", status=200)
        return Response("", status=400)
