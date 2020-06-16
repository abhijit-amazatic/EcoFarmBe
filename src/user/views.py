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
from django.conf import settings

from knox.models import AuthToken
from knox.settings import knox_settings

from core.permissions import UserPermissions
from core.mailer import mail, mail_send
from .models import User, MemberCategory
from vendor.models import Vendor,VendorUser
from .serializers import (UserSerializer, CreateUserSerializer, LogInSerializer, ChangePasswordSerializer, SendMailSerializer, ResetPasswordSerializer, VerificationSerializer, get_encrypted_data)
from integration.crm import (search_query, create_records,)
from integration.box import(get_box_tokens, )
from core.utility import (get_from_crm_insert_to_vendorprofile,NOUN_PROCESS_MAP,get_from_crm_insert_to_account,) 
from slacker import Slacker

KNOXUSER_SERIALIZER = knox_settings.USER_SERIALIZER
slack = Slacker(settings.SLACK_TOKEN)


def notify_admins(email):
    """
    Notify admins on slack & email about new user registration.
    """
    msg = "<!channel>User with the EmailID `%s`  is registered with us.Please review and approve from admin Panel!" % email
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=True)
    mail_send("notify.html",{'link': email},"New User registration.", recipient_list=settings.ADMIN_EMAIL)

    
class GetBoxTokensView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)

class SearchQueryView(APIView):
    """
    Return access token to frontend.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        if request.query_params.get('legal_business_name', None):
            result = search_query('Licenses', request.query_params['legal_business_name'], 'Name')
        elif request.query_params.get('business_dba', None):
            result = search_query('Licenses', request.query_params['business_dba'], 'Business_DBA')
        elif request.query_params.get('license_number', None):
            result = search_query('Licenses', request.query_params['license_number'], 'Legal_Business_Name')
        return Response(result)

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
            instance = serializer.save()
            response = create_records('Contacts', request.data)
            if response['status_code'] == 201:
                instance.is_updated_in_crm = True
                instance.zoho_contact_id = response['response']['data'][0]['details']['id']
                instance.save()
            try:
                if not instance.existing_member:
                    vendor_list = instance.categories.values_list('name', flat=True)
                    vendor_list_lower = [vendor.lower() for vendor in vendor_list]
                    if vendor_list_lower:
                        Vendor.objects.bulk_create([Vendor(ac_manager_id=instance.id, vendor_category=NOUN_PROCESS_MAP[category]) for category in vendor_list_lower])
                        vendors = Vendor.objects.filter(ac_manager__email=instance.email)
                        VendorUser.objects.bulk_create([VendorUser(user_id=instance.id, vendor_id=vendor.id,role='Owner') for vendor in vendors])
                else:
                    get_from_crm_insert_to_vendorprofile.delay(instance.id)
                    get_from_crm_insert_to_account.delay(instance.id)
                link = get_encrypted_data(instance.email)
                mail_send("verification-send.html",{'link': link},"Eco-Farm Verification.", instance.email)
                notify_admins(instance.email)
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

class CategoryView(APIView):

    """
    Get Categories information.
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """
        Display categories.    
        """
        queryset = MemberCategory.objects.values('id','name')
        return Response(queryset)


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
                "existing_member":request.user.existing_member,
                "is_verified":request.user.is_verified,
                "is_approved":request.user.is_approved,
                "status":request.user.status
                
                
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
            link = get_encrypted_data(recipient_email, 'forgot_password')
            subject = "Forgot Password?"
            mail_send(
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
   

class VerificationView(GenericAPIView):
    """
    Verification View
    """
    serializer_class = VerificationSerializer
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Post method for verification view.
        """
        serializer = VerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            response = Response({"Verified successfully!"}, status=200)
        else:
            response = Response("false", status=400)
        return response


    
# def test():
#     #print('in mail test')
#     mail_send("verification-send.html",{'link': 'test'},"Testing",'vikrant.g@amazatic.com')
