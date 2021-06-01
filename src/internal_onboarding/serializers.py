from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, MethodNotAllowed

from phonenumber_field.serializerfields import PhoneNumberField

from brand.models import (
    License,
    Organization,
    ProfileCategory,
)
from .serializers_mixin import InternalOnboardingInviteTokenField



class OrganizationSerializer(serializers.ModelSerializer):
    """
    This defines OrganizationSerializer
    """

    def validate(self, attrs):
        validated_data = super().validate(attrs=attrs)
        if not attrs.get('id'):
            if Organization.objects.filter(name=attrs.get('name', '')).exists():
                raise serializers.ValidationError({'name': 'Organization name already exist'})
        return validated_data

    # def create(self, validated_data):
    #     request = self.context.get('request')
    #     created_by = self.context.get('created_by', request.user)
    #     if request:
    #         validated_data['created_by'] = created_by
    #     return super().create(validated_data)

    class Meta:
        model = Organization
        # read_only_fields = ('created_on', 'updated_on')
        # fields = ('__all__')
        exclude = ('created_by', 'created_on', 'updated_on')


class ContactsSerializer(serializers.Serializer):
    """
    This defines ProgramOverviewSerializer
    """
    zoho_contact = serializers.CharField(max_length=255, required=True)
    roles = serializers.ListField(child=serializers.CharField(), allow_empty=False, required=True)
    send_mail = serializers.BooleanField(required=True)

    class Meta:
        # read_only_fields = ('created_on', 'updated_on')
        fields = (
            'zoho_contact',
            'roles',
            'send_mail',
        )


class InternalOnboardingSerializer(serializers.Serializer):
    """
    Internal Onboarding Serializer.
    """
    zoho_account = serializers.CharField(max_length=255, required=False)
    zoho_vendor = serializers.CharField(max_length=255, required=False)
    license_number = serializers.CharField(max_length=255, required=True)
    license_category = serializers.CharField(max_length=255, required=True)
    ein_or_ssn = serializers.IntegerField(required=True)

    business_structure = serializers.CharField(max_length=255, required=False)

    license_url = serializers.CharField(max_length=255, required=False)
    seller_permit_url = serializers.CharField(max_length=255, required=False)
    w9_url = serializers.CharField(max_length=255, required=False)

    docs_already_on_file = serializers.BooleanField()

    contacts = ContactsSerializer(many=True, required=True)

    organization = OrganizationSerializer()

    def validate_category(self, value):
        queryset = ProfileCategory.objects.filter(name=value)
        if not queryset.exists():
            raise serializers.ValidationError(f'Profile category name \'{value}\' does not exist.')
        return value

    def validate_license_number(self, value):
        queryset = License.objects.filter(license_number=value)
        if queryset.exists():
            raise serializers.ValidationError(f'Profile for license number \'{value}\' already exist.')
        return value

    # def validate_contacts(self, attrs):
    #     if not len(attrs) > 0:
    #         raise serializers.ValidationError('At least one contacts is required')
    #     return attrs

    class Meta:
        fields = (
            'zoho_account',
            'zoho_vendor',
            'license_number',
            'license_category',
            'ein_or_ssn',
            'business_structure',
            'license_url',
            'seller_permit_url',
            'w9_url',
            'docs_already_on_file',
            'contacts',
            'organization',
        )


class InternalOnboardingInviteVerifySerializer(serializers.Serializer):
    """
    Password Retype Serializer to cross check password.
    """
    token = InternalOnboardingInviteTokenField(required=True,)

    class Meta:
        fields = (
            'token',
        )


class InternalOnboardingInviteSetPassSerializer(serializers.Serializer):
    """
    Password Retype Serializer to cross check password.
    """
    token = InternalOnboardingInviteTokenField(required=True,)
    new_password = serializers.CharField(
        label="New Password",
        required=True,
        max_length=128,
        min_length=5,
        style={'input_type': 'password'},
    )
    confirm_password = serializers.CharField(
        label="Confirm New Password",
        required=True,
        max_length=128,
        min_length=5,
        style={'input_type': 'password'},
        write_only=True,
    )
    dob = serializers.DateField(label="Date of Birth", required=True,)
    phone = PhoneNumberField(label="Phone no.", required=True,)


    def validate_confirm_password(self, value):
        """
        Check current password.
        """
        if self.initial_data['password'] != value:
            raise serializers.ValidationError("Password does not match.")
        return value

    class Meta:
        fields = (
            'token',
            'new_password',
            'confirm_password',
            'dob',
            'phone',
        )
