import json
from os import name
import re
import traceback
import datetime
import copy
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission as DjangoPermission
from django.db import (transaction, DatabaseError) 
from django.db.models import Q
from django.forms.models import model_to_dict
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import serializers
from rest_framework import (permissions, viewsets, status, filters, mixins)
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework.decorators import action
from rest_framework.exceptions import (NotFound, PermissionDenied, APIException)
from rest_framework.generics import (GenericAPIView, CreateAPIView,)
from rest_framework.views import APIView
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
# from brand.task_helpers import User

from phonenumber_field.phonenumber import to_python as phonenumber_parse


from integration.crm import (
    get_record,
    search_query,
    get_account_associations,
    get_vendor_associations,
    create_or_update_org_in_crm,
    get_format_dict,
)
from permission.filterqueryset import (filterQuerySet, )
from user.models import (
    User,
    MemberCategory,
)
from brand.models import (
    Organization,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    License,
)
from brand.serializers import (
    LicenseSerializer,
)
from .models import (
    InternalOnboarding,
    InternalOnboardingInvite,
)
from .serializers import (
    InternalOnboardingSerializer,
    InternalOnboardingInviteVerifySerializer,
    InternalOnboardingInviteSetPassSerializer,
)
from .tasks import (
    send_internal_onboarding_invitation,
    create_crm_associations_and_fetch_data,
)

class APIError(Exception):
    """
    exceptions.
    """
    code = 'detail'
    def __init__(self, msg, status_code=400, code=None):
        self.msg = msg
        self.status_code = status_code
        if code:
            self.code = code

    def __str__(self):
        return str(self.msg)

    def get_response(self):
        return Response({self.code: self.msg}, status=self.status_code)




class InternalOnboardingView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    User Invitation Verification View.
    """
    permission_classes = (AllowAny, )
    serializer_class = InternalOnboardingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        vendor_id = data.get('zoho_vendor')
        vendor_data = None
        if vendor_id:
            resp_vendor = get_record(module='Vendors', record_id=vendor_id, full=True)
            if not resp_vendor.get('status_code') == 200:
                return Response({'zoho_vendor': 'Invalid crm vendor id.'}, status=400)
            else:
                vendor_data = resp_vendor.get('response')

        account_id = data.get('zoho_account')
        account_data = None
        if account_id:
            resp_account =  get_record(module='Accounts', record_id=account_id, full=True)
            if not resp_account.get('status_code') == 200:
                return Response({'zoho_account': 'Invalid crm account id.'}, status=400)
            else:
                account_data = resp_account.get('response')


        license_number = data.get('license_number')
        license_id = None
        license_data = {}
        resp_license = search_query('Licenses', license_number, 'Name', is_license=True)
        if not resp_license.get('status_code') == 200:
            return Response({'zoho_vendor': 'Invalid crm License Number.'}, status=400)
        else:
            resp_license_data_ls = resp_license.get('response')
            if resp_license_data_ls and isinstance(resp_license_data_ls, list):
                for resp_license_data in resp_license_data_ls:
                    if license_number == resp_license_data.get('Name'):
                        license_data = resp_license_data
                        license_id = resp_license_data.get('id')
                        break
        if not license_id:
            return Response({'zoho_vendor': 'License Number not found in CRM.'}, status=400)

        org_owner_contact_id = None
        contacts_dict = {}
        constacts_data_dict = {}
        for c in data.get('contacts'):
            c_id = c['zoho_contact']
            resp_contact = get_record(module='Contacts', record_id=c_id, full=True)
            if not resp_contact.get('status_code') == 200:
                return Response({'details': f'Invalid crm contact id: {c_id}.'}, status=400)
            else:
                constacts_data_dict[c_id] = resp_contact.get('response', {})
                if not re.match(r"^([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})$", constacts_data_dict[c_id].get('Email')):
                    return Response(
                        {
                            'details': f"contact {constacts_data_dict[c_id].get('Full_Name')} (id: {c_id}) have invalid email: {constacts_data_dict[c_id].get('Email')}."
                        },
                        status=400
                    )
                phone_number = phonenumber_parse(constacts_data_dict[c_id].get('Phone'))
                if not phone_number.is_valid():
                    return Response(
                        {
                            'details': f"contact {constacts_data_dict[c_id].get('Full_Name')} (id: {c_id}) have invalid phone no.: {constacts_data_dict[c_id].get('Phone')}."
                        },
                        status=400
                    )
                contacts_dict[c_id] = {'roles': c['roles'], 'send_mail': c['send_mail']}
                if not org_owner_contact_id:
                    org_owner_contact_id = c_id

        try:
            with transaction.atomic():
                constacts_user_dict = {}
                for contact_id, contact_data in constacts_data_dict.items():
                    user_defaults = {
                        'phone':             contact_data.get('Phone'),
                        'first_name':        contact_data.get('Full_Name'),
                        'last_name':         contact_data.get('Last_Name'),
                        'full_name':         contact_data.get('Full_Name'),
                        'linkedin':          contact_data.get('Linkedin'),
                        'instagram':         contact_data.get('Instagram'),
                        'facebook':          contact_data.get('Facebook'),
                        'twitter':           contact_data.get('Twitter'),
                        'city':              contact_data.get('Mailing_City'),
                        'state':             contact_data.get('Mailing_State'),
                        'country':           contact_data.get('Mailing_Country'),
                        'zip_code':          contact_data.get('Mailing_Zip'),
                        'zoho_contact_id':   contact_id,
                        'zoho_contact_id':   contact_id,
                        'is_updated_in_crm': True,
                        'existing_member':   True,
                        'crm_link':          f"{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Contacts/{contact_id}/",
                        'membership_type':   User.CATEGORY_BUSINESS,
                    }
                    user, created = User.objects.get_or_create(email=contact_data.get('Email'), defaults=user_defaults)
                    if created:
                        user.set_unusable_password()
                    mem_cat = MemberCategory.objects.filter(name__in=contact_data.get('Contact_Type'))
                    user.categories.add(*mem_cat)
                    constacts_user_dict[contact_id] = (user, created)

                organization_id = None
                organization_obj = None
                if not data['organization'].get('id'):
                    organization_create_data = copy.deepcopy(data['organization'])
                    if 'id' in organization_create_data:
                        organization_create_data.pop('id')
                    organization_create_data['created_by'] = constacts_user_dict[org_owner_contact_id][0]
                    organization_obj = Organization.objects.create(**organization_create_data)
                    create_or_update_org_in_crm(organization_obj)
                    organization_id = organization_obj.zoho_crm_id
                else:
                    organization_obj = Organization.objects.get(data['organization']['id'])
                    if not organization_obj.zoho_crm_id:
                        create_or_update_org_in_crm(organization_obj)
                    organization_id = organization_obj.zoho_crm_id

                if not organization_id:
                    raise APIError('Unable to get organization crm id')

                license_create_data = {
                    'created_by':          request.user,
                    'organization':        organization_obj,
                    'license_number':      license_number,
                    'zoho_crm_id':         license_id,
                    'legal_business_name': license_data.get('Legal_Business_Name',''),
                    'ein_or_ssn':          data.get('ein_or_ssn'),
                    'tax_identification':  data.get('tax_identification'),
                    'is_seller':           data.get('is_seller'),
                    'is_buyer':            data.get('is_buyer'),
                    'profile_category':    data.get('license_category'),
                }

                license_obj = License.objects.create(**license_create_data)

                for k, v in get_format_dict('Licenses_To_DB').items():
                    if k in license_obj.__dict__ and k not in ('license_number', 'legal_business_name'):
                        license_obj.__dict__[k] = license_data.get(v)
                license_obj.step = 1
                license_obj.save()

                invite_id_list = []
                for contact_id, (user, created) in constacts_user_dict.items():
                    organization_user, _ = OrganizationUser.objects.get_or_create(
                        organization=organization_obj,
                        user=user,
                    )
                    roles_ls = []
                    for role_name in contacts_dict[contact_id]['roles']:
                        role, _ = OrganizationRole.objects.get_or_create(organization=organization_obj, name=role_name)
                        roles_ls.append(role)
                        organization_user_role, _ = OrganizationUserRole.objects.get_or_create(
                            organization_user=organization_user,
                            role=role,
                        )
                        organization_user_role.licenses.add(license_obj)
                    inv_obj = InternalOnboardingInvite.objects.create(
                        organization=organization_obj,
                        user=user,
                        license=license_obj,
                        created_by=request.user,
                        is_user_created=created,
                        is_user_do_onboarding=contacts_dict[contact_id]['send_mail'],
                    )
                    inv_obj.roles.add(*roles_ls)
                    invite_id_list.append(inv_obj.id)


                InternalOnboarding.objects.create(
                    license_number=license_number,
                    submitted_data=request.data,
                    created_by=request.user,
                )

                # raise APIError('testing')
        except DatabaseError as e:
            return Response({'details': f'Error: {e}'}, status=400)
        except APIError as e:
            return e.get_response()
        else:
            send_internal_onboarding_invitation.delay(invite_id_list)
            create_crm_associations_and_fetch_data.delay(
                create_crm_associations_kwargs={
                    'vendor_id':         vendor_id,
                    'account_id':        account_id,
                    'license_id':        license_id,
                    'org_id':            organization_id,
                    'contacts_dict':      contacts_dict,
                    'constacts_data_dict': {ck: {k: v for k, v in cv.items() if k in ('Contact_Company_Role',)} for ck, cv in constacts_data_dict.items()},
                    'vendor_data':       vendor_data,
                    'account_data':      account_data,
                },
                fetch_data_kwargs={
                    'user_id': request.user.id,
                    'license_number': license_number,
                    'license_obj_id': license_obj.id,
                },
            )
            lic_serializer = LicenseSerializer(license_obj, context=self.get_serializer_context())
            return Response(lic_serializer.data)

    @action(
        detail=False,
        methods=['post'],
        name='Invite Verify',
        url_name='internal-onboarding-invite-verify',
        url_path='invite-verify',
        permission_classes=(AllowAny,),
        serializer_class=InternalOnboardingInviteVerifySerializer
    )
    def invite_verify(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,)
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['token']
        user = instance.user
        response_data = {
            # 'new_user': True if not user.last_login else False,
            'is_new_user': not user.has_usable_password() and not user.last_login,
            'user': {
                'email': user.email,
                'full_name': user.get_full_name(),
                'phone': user.phone.as_e164,
                'dob': user.date_of_birth,
            },
        }
        if instance.status in ('pending',):
            user.is_verified = True
            user.save()
            instance.completed_on = timezone.now()
            instance.status = 'completed'
            instance.save()
            response_data['detail'] = 'Accepted'
            response = Response(response_data, status=status.HTTP_200_OK)
        elif instance.status == 'completed':
            response_data['detail'] = 'Already accepted'
            response = Response(response_data, status=status.HTTP_200_OK)
        else:
            response = Response({'detail': 'invalid token'}, status=400)
        return response

    @action(
        detail=False,
        methods=['post'],
        name='Set Password',
        url_name='internal-onboarding-invite-set-pass',
        url_path='invite-set-password',
        permission_classes=(AllowAny,),
        serializer_class=InternalOnboardingInviteSetPassSerializer,
    )
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,)
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['token']
        user = instance.user
        if instance.status == 'completed':
            if not user.has_usable_password():
                with transaction.atomic():
                    user.date_of_birth = serializer.validated_data['dob']
                    user.phone = serializer.validated_data['phone']
                    user.save()
                    user.set_password(serializer.validated_data['new_password'])
                response = Response({'detail': 'Password is set successfully'}, status=200)
            else:
                response = Response({'detail': 'Already have a password set for this account'}, status=400)
        else:
            response = Response({'detail': 'Invite is not completed'}, status=400)
        return response