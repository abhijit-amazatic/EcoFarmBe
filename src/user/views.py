"""
All views related to the User defined here.
"""
import json
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
from rest_framework.viewsets import (ModelViewSet, ReadOnlyModelViewSet)
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import (filters,)
from django_filters import (FilterSet)
from django_filters.rest_framework import DjangoFilterBackend
from utils.pagination import PaginationHandlerMixin
from django.conf import settings
from django.utils import timezone
from knox.models import AuthToken
from knox.settings import knox_settings
from django.db.models import Q
from core.permissions import UserPermissions
from core.mailer import mail, mail_send
from .models import (User, MemberCategory, PrimaryPhoneTOTPDevice, TermsAndConditionAcceptance, TermsAndCondition, HelpDocumentation,)
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    LogInSerializer,
    ChangePasswordSerializer,
    SendMailSerializer,
    ResetPasswordSerializer,
    VerificationSerializer,
    get_encrypted_data,
    SendVerificationSerializer,
    PhoneNumberSerializer,
    PhoneNumberVerificationSerializer,
    TermsAndConditionAcceptanceSerializer,
    HelpDocumentationSerializer,
)
from permission.filterqueryset import (filterQuerySet, )
from integration.crm import (search_query, create_records, update_records)
from integration.box import(get_box_tokens, )
from core.utility import (NOUN_PROCESS_MAP,send_verification_link,send_async_user_approval_mail,get_from_crm_insert_to_vendor_or_account,)
from slacker import Slacker
from brand.models import (License,Organization,)

KNOXUSER_SERIALIZER = knox_settings.USER_SERIALIZER
slack = Slacker(settings.SLACK_TOKEN)


class BasicPagination(PageNumberPagination):
    """
    Pagination class. 
    """
    page_size_query_param = 'limit'
    page_size = 50

def notify_admins(email,crm_link):
    """
    Notify admins on slack & email about new user registration.
    """
    msg = "<!channel>*User with the EmailID `%s`  is registered with us!*\n* Contact CRM Link is:* <%s>" % (email,crm_link)
    slack.chat.post_message(settings.SLACK_CHANNEL_NAME,msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)
    #mail_send("notify.html",{'link': email},"New User registration.", recipient_list=settings.ADMIN_EMAIL)

def get_update_db_contact(instance,response,status):
    """
    update db contact related data & return crm link.
    """
    try:
        if status == 'new':
            #print('in new contact+response',instance,'\n',response,'\n',status)
            instance.is_updated_in_crm = True
            instance.zoho_contact_id = response['response']['data'][0]['details']['id']
            link = settings.ZOHO_CRM_URL+"/crm/org"+settings.CRM_ORGANIZATION_ID+"/tab/Contacts/"+response['response']['data'][0]['details']['id']+"/"
            instance.crm_link = link
            instance.save()
            return link
        elif status == 'exist':
            instance.is_updated_in_crm = True
            instance.zoho_contact_id = response['response'][0].get('id')
            link = settings.ZOHO_CRM_URL+"/crm/org"+settings.CRM_ORGANIZATION_ID+"/tab/Contacts/"+response['response'][0].get('id')+"/"
            instance.crm_link = link
            instance.save()
            return link
    except Exception as e:
        print('Exception while crm link db save', e)
        
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
            result = search_query('Licenses', request.query_params['legal_business_name'], 'Legal_Business_Name')
        elif request.query_params.get('business_dba', None):
            result = search_query('Licenses', request.query_params['business_dba'], 'Business_DBA', True)
        elif request.query_params.get('license_number', None):
            license_number = request.query_params['license_number'].strip()
            is_allow_all = request.query_params.get('is_allow_all', False)
            if is_allow_all in [True, 'true']:
                result = search_query('Licenses', license_number, 'Name', is_license=True)
                return Response(result)
            try:
                is_license_in_db = License.objects.filter(license_number=license_number).exists()
            except License.DoesNotExist:
                is_license_in_db = False
            if is_license_in_db:
                return Response({
                    'error': 'License already in database.'
                }, status=status.HTTP_400_BAD_REQUEST)
            result = search_query('Licenses', license_number, 'Name', is_license=True)
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
            contact = search_query('Contacts', request.data.get('email'), 'Email')
            request.data['Contact_Type'] = [i['name'] for i in instance.categories.values()]
            if contact['status_code'] == 200:
                request.data['id'] = contact.get('response')[0].get('id')
                response = update_records('Contacts', request.data)
                crm_db_update_link = get_update_db_contact(instance,contact,'exist')
            else:
                create_response = create_records('Contacts', request.data)
                if create_response['status_code'] == 201:
                    crm_db_update_link = get_update_db_contact(instance,create_response,'new')
            try:
                link = get_encrypted_data(instance.email)
                mail_send("verification-send.html",{'link': link,'full_name': instance.full_name},"Thrive Society Verification.", instance.email)
                notify_admins(instance.email,crm_db_update_link)
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

    def search(self,name,items):
        return [element for element in items if element['name'] == name]
    
    def get(self, request):
        """
        Display categories.    
        """
        category_order = ['Cultivator','Nursery', 'Processor','Distributor','Manufacturer','Retailer','Testing','Transporter','Events', 'Brand', 'Hemp', 'Ancillary Products', 'Ancillary Services', 'Investor', 'Patient', 'Healthcare' ]
        items = MemberCategory.objects.values()
        ordered_response= []
        for category in category_order:
            ordered_response.append(self.search(category,items)[0])
        return Response(ordered_response)
    

class PendoView(APIView):
    
    """
    Get Logged in user's information for pendo mapping.
    """

    def get(self, request):
        """
        Map data according to pendo structure.
        """
        qs_license = filterQuerySet.for_user(License.objects.all(), request.user)
        qs_org = filterQuerySet.for_user(Organization.objects.all(), request.user)
        return Response({
            "has_access_to_organizations":qs_org.values_list('name', flat=True).distinct(),
            "created_organizations":qs_org.filter(created_by=request.user).values_list('name',flat=True).distinct(),
            "has_access_to_license_names":qs_license.values_list('legal_business_name', flat=True).distinct(),
            "created_license_names":qs_license.filter(created_by=request.user).values_list('legal_business_name',flat=True).distinct(),
            "has_access_to_license_numbers":qs_license.values_list('license_number', flat=True).distinct(),
            "created_license_numbers":qs_license.filter(created_by=request.user).values_list('license_number',flat=True).distinct(),
            "associated_profile_categories":qs_license.values_list('profile_category', flat=True).distinct()
        }, status=200)


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
                "is_phone_verified":request.user.is_phone_verified,
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

class SendVerificationView(APIView):
    """
    Send Verification link
    """
    serializer_class = SendVerificationSerializer
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Post method for verification view link.
        """
        serializer = SendVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            send_verification_link(request.data.get('email'))
            response = Response({"Verification link sent!"}, status=200)
        else:
            response = Response("false", status=400)
        return response
    

class GetPhoneNumberVerificationCodeSMSView(GenericAPIView):
    """
    Send Verification SMS
    """
    serializer_class = PhoneNumberSerializer
    permission_classes = (AllowAny,)
    def post(self, request):
        """
        Post method for verification SMS
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(phone=serializer.validated_data['phone_number'])
            device, _ = PrimaryPhoneTOTPDevice.objects.get_or_create(user=user)
            if not device.confirmed:
                device.send_otp(event_code='phone_verification')
                return Response({"Verification SMS sent!"}, status=200)
            else:
                return Response("Phone is already Verified!", status=400)
        except User.DoesNotExist:
            return Response({"detail": "Phone number in not registered."}, status=404)


class GetPhoneNumberVerificationCodeCallView(GenericAPIView):
    """
    Send Verification SMS
    """
    serializer_class = PhoneNumberSerializer
    permission_classes = (AllowAny,)
    def post(self, request):
        """
        Post method for verification SMS
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(phone=serializer.validated_data['phone_number'])
            device, _ = PrimaryPhoneTOTPDevice.objects.get_or_create(user=user)
            if not device.confirmed:
                device.send_otp_call(event_code='phone_verification')
                return Response({"Verification call request made!"}, status=200)
            else:
                return Response("Phone is already Verified!", status=400)
        except User.DoesNotExist:
            return Response({"detail": "Phone number in not registered."}, status=404)
         
class PhoneNumberVerificationView(GenericAPIView):
    """
    Verification View 
    """
    serializer_class = PhoneNumberVerificationSerializer
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Post method for verification view.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(phone=serializer.validated_data['phone_number'])
            device, _ = PrimaryPhoneTOTPDevice.objects.get_or_create(user=user)
            if device.verify_token(serializer.validated_data['code'], event_code='phone_verification'):
                user.is_phone_verified = True
                if user.is_verified:
                    user.is_approved = True
                    user.approved_on = timezone.now()
                    user.approved_by = {'email':"connect@thrive-society.com(Automated-Bot)"}
                    send_async_user_approval_mail.delay(user.id)
                user.save()
                return Response({"Phone Verified successfully!"}, status=200)
            else:
                return Response({"detail": "Verification code dit not match."}, status=400)
        except User.DoesNotExist:
            return Response({"detail": "Phone number in not registered."}, status=404)


class TermsAndConditionAcceptanceView(APIView):
    """
    Terms and condition acceptance view.
    """
    serializer_class = TermsAndConditionAcceptanceSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Post method for create terms and condition acceptance entry
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        TermsAndConditionAcceptance.objects.create(
            user=self.request.user,
            terms_and_condition=getattr(serializer, 'tac_obj'),
            is_accepted=serializer.validated_data['is_accepted'],
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            hostname=request.META.get('REMOTE_HOST'),
        )
        return Response(status=201)

    def get(self, request):
        """
        Get method list terms and condition acceptances
        """
        bypass_qs = User.objects.filter(id=self.request.user.id,bypass_terms_and_conditions=True)
        if bypass_qs.exists():
            return Response({'is_accepted': True}, status=200)
        
        qs = TermsAndConditionAcceptance.objects.filter(
            user=self.request.user,
            terms_and_condition__profile_type='other',
        )
        if qs.exists():
            instance = qs.latest('created_on')
            return Response({'is_accepted': instance.is_accepted}, status=200)
        
        qs = TermsAndCondition.objects.filter(
                profile_type='other',
                publish_from__lte=timezone.now().date(),
        )
        if qs.exists():
            instance = qs.latest('publish_from')
            return Response({'terms_and_condition': instance.terms_and_condition}, status=200)
        

class HelpDocumentationView(ReadOnlyModelViewSet):
    """
    Return help docs.
    """
    #pagination_class = BasicPagination
    #PaginationHandlerMixin
    queryset = HelpDocumentation.objects.all()
    serializer_class = HelpDocumentationSerializer
    filter_backends = [filters.OrderingFilter,DjangoFilterBackend]
    filterset_fields = ['title', 'url', 'for_page','ordering']
    permission_classes = (AllowAny,)
    #ordering = 'title'


