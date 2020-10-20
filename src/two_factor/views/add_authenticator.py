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

from ..conf import settings
from ..models import (
    AddAuthenticatorRequest,
    AuthenticatorTOTPDevice,
)
from ..serializers import (
    AddAuthenticatorRequestSerializer,
    TokenSerializer,
    EmptySerializer,
)


class AddAuthenticatorRequestViewSet(mixins.CreateModelMixin,
                                 mixins.RetrieveModelMixin,
                                 GenericViewSet):
    """
    View
    """
    serializer_class = AddAuthenticatorRequestSerializer
    permission_classes = (IsAuthenticated,)
    queryset = AddAuthenticatorRequest.objects.all()
    lookup_field = 'request_id'
    lookup_url_kwarg = 'request_id'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        name='Get QRString',
        url_name='add-authenticator-qrstring',
        url_path='qrstring',
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
        name='Get QRCode',
        url_name='add-authenticator-qrcode',
        url_path='qrcode',
        serializer_class=EmptySerializer,
    )
    def get_qrcode(self, request, *args, **kwargs):
        """
        Authy user registration QRCode.
        """
        add_authenticator_request = self.get_object()
        if add_authenticator_request.status == 'pending':
            device = add_authenticator_request.get_device()
            if device and isinstance(device, AuthenticatorTOTPDevice):
                image_content_types = {
                    'PNG': 'image/png',
                    'SVG': 'image/svg+xml; charset=utf-8',
                }
                image_factory = qrcode.image.svg.SvgPathFillImage

                img = qrcode.make(
                    device.config_url,
                    image_factory=image_factory
                )
                resp = HttpResponse(
                    content_type=image_content_types[image_factory.kind])
                img.save(resp)
                return resp
            return Response({'detail': 'unable to get device'}, status=400)
        else:
            return Response({"detail": f"request is {add_authenticator_request.status}."}, status=400)

    @action(
        detail=True,
        methods=['post'],
        name='Confirm Request',
        url_name='add-authenticator-request-confirm',
        url_path='verify',
        serializer_class=TokenSerializer,
    )
    def verify(self, request, *args, **kwargs):
        """
        Get authy user registration status.
        """
        add_authenticator_request = self.get_object()
        if add_authenticator_request.status == 'pending':
            serializer_context = self.get_serializer_context()
            serializer = self.serializer_class(
                data=request.data,
                context=serializer_context,
            )
            serializer.is_valid(raise_exception=True)
            token = serializer.validated_data.get('token', '')
            device = add_authenticator_request.get_device()
            if device and isinstance(device, AuthenticatorTOTPDevice):
                if device.verify_token(token=token, commit=False):
                    AuthenticatorTOTPDevice.objects.filter(user=self.request.user).delete()
                    device.confirmed = True
                    device.save()
                    add_authenticator_request.is_completed = True
                    add_authenticator_request.save()
                    response = Response({'detail': 'device added successfully'}, status=200)
                else:
                    response = Response({'detail': 'Verification failed'}, status=400)
            else:
                response = Response({'detail': 'unable to get device'}, status=400)
        else:
            response = Response({"detail": f"request is {add_authenticator_request.status}."}, status=400)
        return response