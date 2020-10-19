
"""
All views related to the two factor authorization defined here.
"""
import jwt
from rest_framework.permissions import (AllowAny, )
from rest_framework.response import Response
from rest_framework.views import APIView
from authy.api import AuthyApiClient

from ..conf import settings
from ..utils import (
    validate_authy_callback_request_signature
)
from ..models import (
    AuthyUser,
    AuthyAddUserRequest,
    AuthyOneTouchDevice,
    AuthyOneTouchRequest,
)

authy_api = AuthyApiClient(settings.AUTHY_ACCOUNT_SECURITY_API_KEY)



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
            return Response({}, status=200)
        return Response({}, status=400)


class AuthyUserRegistrationCallbackView(APIView):
    """
    View
    """
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Post method view.
        """
        if 'body' in request.data and 0:
            try:
                data = jwt.decode(
                    request.data['body'],
                    getattr(settings, 'AUTHY_USER_REGISTRATION_CALLBACK_SIGNING_KEY', ''),
                    algorithms=['HS256']
                )
            except jwt.PyJWTError:
                pass
            else:
                scheme = request.META.get('HTTP_X_FORWARDED_PROTO', request.scheme)
                url = f'{scheme}://{request.get_host()}{request.path}'
                if data['url'] == url:
                    for event in data['params']['events']:
                        if  event['event']=='user_registration_completed':
                            registration = event['objects']['registration']
                            req_instance = AuthyAddUserRequest.objects.filter(custom_user_id=registration['s_custom_id']).first()
                            if req_instance and req_instance.status == 'pending':
                                req_instance.is_registered = True
                                req_instance.authy_id = str(registration['s_authy_id'])
                                if req_instance.is_registered:
                                    authy_user, _ = AuthyUser.objects.get_or_create(
                                    authy_id=req_instance.authy_id)
                                    try:
                                        device = AuthyOneTouchDevice.objects.get(user=req_instance.user)
                                    except AuthyOneTouchDevice.DoesNotExist:
                                        device = AuthyOneTouchDevice.objects.create(
                                            user=req_instance.user, authy_user=authy_user, confirmed=True)
                                    else:
                                        device.authy_user = authy_user
                                        device.confirmed = True
                                        device.save()
                                    req_instance.save()

                                return Response({}, status=200)
        return Response({}, status=400)
