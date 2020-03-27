"""
All views related to the User defined here.
"""
import json
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.viewsets import (ModelViewSet,)
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from knox.models import AuthToken
from knox.settings import knox_settings

from core.permissions import UserPermissions
from core.mailer import mail
from .models import User
from .serializers import (
    UserSerializer, CreateUserSerializer, LogInSerializer, ChangePasswordSerializer, SendMailSerializer, ResetPasswordSerializer, FeedbackSerializer, RequestAppSerializer)


from core.permissions import IsAuthenticatedSitePermission

KNOXUSER_SERIALIZER = knox_settings.USER_SERIALIZER
hs = HubspotClient()
amp = AmplitudeClient()

class UserViewSet(ModelViewSet):
    """
    User view set used for CRUD operations.
    """
    permission_classes = (UserPermissions,)

    def get_queryset(self):
        query_set = User.objects.filter(is_active=True)
        if self.request.user.is_superuser:
            return query_set
        return query_set.filter(email=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    def create(self, request):
        """
        This view is  used to create user.
        """
        serializer = CreateUserSerializer(
            data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                deal_id = hs.create_or_update_deal(request.data['email'])
                user = User.objects.get(email=request.data['email'])
                user.associated_hs_deal_id = deal_id
                user.save()
                property_data = json.dumps({
                    "properties": [
                        {
                            "property": "signed_up",
                            "value": "Yes"
                        }
                    ]
                })
                hs.update_contact_property_generic(property_data,user.email)
                amp.update_or_create_user_properties(user)
            except Exception as e:
                print(e)
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):

    """
    Get Logged in user's information.
    """

    def get(self, request):
        """
        Logged in user's info.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=200)


class LogInView(APIView):

    """
    Login View.
    """
    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = LogInSerializer

    def post(self, request):
        """"
        Post method for login.
        """
        serializer = LogInSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            token = AuthToken.objects.create(request.user)
            response = Response({
                "user": KNOXUSER_SERIALIZER(request.user).data,
                "token": token,
            })
        else:
            response = Response({"data": serializer.errors})
        return response


class ChangePasswordView(GenericAPIView):
    """
    Api view for change password.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def get_queryset(self):
        return

    def post(self, request):
        """
        Post method for Password view.
        """
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            response = Response({"Password Changed Successfully!"}, status=200)
        else:
            response = Response({"Something went wrong!"}, status=400)
        return response


class SendMailView(GenericAPIView):
    """
    Send Mail View
    """
    serializer_class = SendMailSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        post method for email compose.
        """
        serializer = SendMailSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            recipient_email = serializer.data.get('email')
            link = serializer.get_encrypted_data(recipient_email)
            subject = "Forgot Password?"
            mail(
                "email-send.html",
                {
                    # 'first_name': recipient_email.capitalize(),
                    'link': link
                }, subject, recipient_email
            )
            response = Response(
                {"The mail has been sent successfully"}, status=200)
        else:
            response = Response({"data": serializer.errors})
        return response


class ResetPasswordView(GenericAPIView):
    """
    Reset Password View
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return

    def post(self, request):
        """
        Post method for Password view
        """
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            response = Response({"Updated successfully!"}, status=200)
        else:
            response = Response("false", status=400)
        return response

    
class FeedbackView(APIView):

    """
    Post Logged in user's Feedback .
    """
    permission_classes = (IsAuthenticatedSitePermission,)
    serializer_class = FeedbackSerializer
    
    def post(self, request):
        """
        This endpoint is used to post Feedback in Hubspot.
        """
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            hubspot = HubspotClient()
            hubspot_update  = hubspot.update_contact_feedback_properties(request.data.get('feedback_type'), request.data.get('feedback_comments'),request.user.email)
            if hubspot_update is True:
                return Response({"Success": "Feedback Submitted Successfully!"}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response(hubspot_update, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestAppView(APIView):

    """
    Post Requested app in HS.
    """
    permission_classes = (IsAuthenticatedSitePermission,)
    serializer_class = RequestAppSerializer
    
    def post(self, request):
        """
        This endpoint is used to post app requested in Hubspot.
        """
        serializer = RequestAppSerializer(data=request.data)
        if serializer.is_valid():
            is_updated  = hs.update_request_app_property(request.data.get('requested_connection'),request.user.email)
            if is_updated is True:
                return Response({"Success": "App requested Successfully!"}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response({"Something went wrong(Requesting contact may not present in HS!)"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
