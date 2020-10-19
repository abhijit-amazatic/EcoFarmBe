
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
from authy.api import AuthyApiClient

from ..conf import settings
from ..models import (
    AuthyUser,
    AuthyAddUserRequest,
    AuthyOneTouchDevice,
    AuthySoftTOTPDevice,
)
from ..serializers import (
    AuthyAddUserRequestSerializer,
    EmptySerializer,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)


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
        url_name='authy-user-registration-status-update',
        url_path='get-registration-status',
        serializer_class=EmptySerializer,
    )
    def get_registration_status(self, request, *args, **kwargs):
        """
        Get authy user registration status.
        """
        instance = self.get_object()
        if instance.status == 'pending':
            authy_user = authy_api.users.registration_status(
                custom_user_id=instance.custom_user_id
            )
            if authy_user.ok():
                instance.authy_id = authy_user.content['registration']['authy_id']
                instance.is_registered = authy_user.content['registration']['status'] == 'completed'
                if instance.is_registered:
                    authy_user, _ = AuthyUser.objects.get_or_create(authy_id=instance.authy_id)
                    try:
                        device = AuthyOneTouchDevice.objects.get(user=instance.user)
                    except AuthyOneTouchDevice.DoesNotExist:
                        pass
                    else:
                        device.delete()
                    device = AuthyOneTouchDevice.objects.create(
                        user=instance.user, authy_user=authy_user, confirmed=True)
                    try:
                        device = AuthySoftTOTPDevice.objects.get(user=instance.user)
                    except AuthySoftTOTPDevice.DoesNotExist:
                        pass
                    else:
                        device.delete()
                    device = AuthySoftTOTPDevice.objects.create(
                        user=instance.user, authy_user=authy_user, confirmed=True)
                    instance.save()

        response = Response({'status': instance.status}, status=200)
        return response

    # @action(
    #     detail=True,
    #     methods=['get'],
    #     name='Get Registration Status',
    #     url_name='authy-user-registration-status',
    #     url_path='get-registration-status',
    #     serializer_class=EmptySerializer,
    # )
    # def get_registration_status(self, request, *args, **kwargs):
    #     """
    #     Get authy user registration status.
    #     """
    #     instance = self.get_object()
    #     response = Response({'status': instance.status}, status=200)
    #     return response
