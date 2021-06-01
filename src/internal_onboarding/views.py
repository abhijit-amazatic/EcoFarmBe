import json
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
from rest_framework.exceptions import (NotFound, PermissionDenied,)
from rest_framework.generics import (GenericAPIView, CreateAPIView,)
from rest_framework.views import APIView
from rest_framework.permissions import (AllowAny, IsAuthenticated, )
from rest_framework.response import Response
# from brand.task_helpers import User

from phonenumber_field.phonenumber import to_python as phonenumber_parse


from user.models import (
    User,
    MemberCategory,
)
from integration.crm import (
    get_record,
    search_query,
    get_account_associations,
    get_vendor_associations,
    create_or_update_org_in_crm,
)
from permission.filterqueryset import (filterQuerySet, )
from brand.models import (
    Organization,
    OrganizationUser,
    OrganizationUserRole,
    OrganizationUserInvite,
)
from .models import (
    InternalOnboardingInvite,
)
from .serializers import (
    InternalOnboardingSerializer,
    InternalOnboardingInviteVerifySerializer,
    InternalOnboardingInviteSetPassSerializer,
)


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

        account_id = data.get('zoho_account')
        account_data = None
        account_associations = {}
        if account_id:
            resp_account =  get_record(module='Accounts', record_id=account_id, full=True)
            if not resp_account.get('status_code') == 200:
                return Response({'zoho_account': 'Invalid crm account id.'}, status=400)
            else:
                account_data = resp_account.get('response')
                account_associations = get_account_associations(account_id=account_id, brands=False)

        vendor_id = data.get('zoho_vendor')
        vendor_data = None
        vendor_associations = {}
        if vendor_id:
            resp_vendor =  get_record(module='Vendors', record_id=account_id, full=True)
            if not resp_vendor.get('status_code') == 200:
                return Response({'zoho_vendor': 'Invalid crm vendor id.'}, status=400)
            else:
                vendor_data = resp_vendor.get('response')
                vendor_associations = get_vendor_associations(vendor_id=vendor_id, brands=False, cultivars=False)

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
        for c in data.get['contacts']:
            c_id = c['zoho_contact']
            resp_contact = get_record(module='Contacts', record_id=c_id, full=True)
            if not resp_contact.get('status_code') == 200:
                return Response({'details': f'Invalid crm contact id: {c_id}.'}, status=400)
            else:
                constacts_data_dict[c_id] = resp_account.get('response', {})
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
                        'phone': contact_data.get('Phone'),
                        'first_name': contact_data.get('Full_Name'),
                        'last_name': contact_data.get('Last_Name'),
                        'full_name': contact_data.get('Full_Name'),

                        'linkedin': contact_data.get('Linkedin'),
                        'instagram': contact_data.get('Instagram'),
                        'facebook': contact_data.get('Facebook'),
                        'twitter': contact_data.get('Twitter'),

                        'city': contact_data.get('Mailing_City'),
                        'state': contact_data.get('Mailing_State'),
                        'country': contact_data.get('Mailing_Country'),
                        'zip_code': contact_data.get('Mailing_Zip'),

                        'zoho_contact_id': contact_id,
                        'zoho_contact_id': contact_id,
                        'is_updated_in_crm': True,
                        'existing_member': True,
                        'crm_link': f"{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Contacts/{contact_id}/",
                        'membership_type': User.CATEGORY_BUSINESS,
                    }
                    user, created = User.objects.get_or_create(email=contact_data.get('Email'), defaults=user_defaults)
                    if created:
                        user.set_unusable_password()
                    mem_cat = MemberCategory.objects.filter(name__in=contact_data.get('Contact_Type'))
                    user.categories.add(*mem_cat)
                    constacts_user_dict[contact_id] = (user, created)

                if not data['organization']['id']:
                    organization_create_data = copy.deepcopy(data['organization'])
                    organization_create_data.pop('id')
                    organization_create_data['created_by'] = constacts_user_dict[org_owner_contact_id][0]
                    organization_obj = Organization.objects.create(**organization_create_data)
                    create_or_update_org_in_crm(organization_obj)

        except DatabaseError as e:
            return Response({'detail': f'Error: {e}'}, status=400)

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
            'new_user': True if not user.last_login else False,
            'is_password_set': user.has_usable_password(),
            'email': user.email,
            'full_name': user.get_full_name(),
        }
        if instance.status in ('pending',):
            organization_user, _ = OrganizationUser.objects.get_or_create(
                organization=instance.organization,
                user=user,
            )

            for role in instance.roles.all():
                organization_user_role, _ = OrganizationUserRole.objects.get_or_create(
                    organization_user=organization_user,
                    role=role,
                )
                organization_user_role.licenses.add(instance.license)
                instance.completed_on = timezone.now()
            instance.status = 'completed'
            instance.save()
            response_data['detail'] = 'Accepted'
            response = Response(response_data, status=status.HTTP_200_OK)
        elif instance.status == 'completed':
            response = Response({'detail': 'Already accepted'},status=200)
        else:
            response = Response({'detail': 'invalid token'},status=400)
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
            if not user.last_login and not user.has_usable_password():
                with transaction.atomic():
                    user.date_of_birth = serializer.validated_data['dob']
                    user.phone = serializer.validated_data['phone']
                    user.save()
                    user.set_password(serializer.validated_data['new_password'])
                response = Response({'detail': 'Password set successfull'}, status=200)
            else:
                response = Response({'detail': 'Already have a password for this account'}, status=400)
        else:
            response = Response({'detail': 'Invite is not completed'}, status=400)
        return response