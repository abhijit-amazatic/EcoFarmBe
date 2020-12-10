"""
Serializer to validate brand related modules.
"""

import requests
from django.conf import settings
from tempfile import TemporaryFile

from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from core.settings import (AWS_BUCKET, )
from .models import (Brand, License, LicenseUser, ProfileContact, LicenseProfile,
                     CultivationOverview, ProgramOverview, FinancialOverview, CropOverview, ProfileReport)
from .models import (LicenseRole,)
from user.models import User
from inventory.models import (Documents, )
from core.utility import (notify_admins_on_profile_registration,)
from integration.crm import (insert_vendors, insert_accounts,)
from integration.box import upload_file
from integration.books import(create_customer_in_books, )
from integration.apps.aws import (create_presigned_url, )


def insert_or_update_vendor_accounts(profile,instance):
    """
    Insert/update vendors/accounts based on existing user or not. 
    """
    if profile.license.created_by.existing_member:
        if profile.license.profile_category == 'cultivation':
            if instance.brand:
                insert_vendors.delay(id=instance.brand.id,is_update=True)
            else:
                insert_vendors.delay(id=instance.id, is_single_user=True, is_update=True)
        else:
            if instance.brand:
                insert_accounts.delay(id=instance.brand.id,is_update=True)
            else:
                insert_accounts.delay(id=instance.id, is_single_user=True,is_update=True)
    elif not profile.license.created_by.existing_member:
        if profile.license.profile_category == 'cultivation':
            if instance.brand:
                insert_vendors.delay(id=instance.brand.id)
            else:
                insert_vendors.delay(id=instance.id, is_single_user=True)
        else:
            if instance.brand:
                insert_accounts.delay(id=instance.brand.id)
            else:
                insert_accounts.delay(
                    id=instance.id, is_single_user=True)
                
        
class BrandSerializer(serializers.ModelSerializer):
    """
    This defines Brand serializer.
    """
    document_url = serializers.SerializerMethodField()

    def get_document_url(self, obj):
        """
        Return s3 document url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='profile_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def validate(self, data):
        if self.partial:
            pass
        return data

    class Meta:
        model = Brand
        fields = ('__all__')


class BrandCreateSerializer(serializers.ModelSerializer):
    """
    This defines Brand creation serializer and related validation
    """

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to create Brand only with self foreign key.
        """
        if not (obj['ac_manager'] == self.context['request'].user) and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
            raise serializers.ValidationError(
                "You are not allowed to create brand with another user!")
        return obj

    class Meta:
        model = Brand
        fields = ('__all__')


class LicenseSerializer(serializers.ModelSerializer):
    """
    This defines license serializer.
    """
    license_url = serializers.SerializerMethodField()
    seller_permit_url = serializers.SerializerMethodField()
    license_profile_url = serializers.SerializerMethodField()
    is_existing_user = serializers.SerializerMethodField()


    def get_is_existing_user(self, obj):
        """
        return if user is existing user.
        """
        return obj.created_by.existing_member
    
    def get_license_profile_url(self, obj):
        """
        Return s3 license url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='profile_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None
    
    def get_license_url(self, obj):
        """
        Return s3 license url.
        """
        try:
            license = Documents.objects.filter(object_id=obj.id, doc_type='license').latest('created_on')
            if license.box_url:
                return license.box_url
            else:
                path = license.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def get_seller_permit_url(self, obj):
        """
        Return s3 license url.
        """
        try:
            seller = Documents.objects.filter(object_id=obj.id, doc_type='seller_permit').latest('created_on')
            if seller.box_url:
                return seller.box_url
            else:
                path = seller.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None
    
    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to create license only with respective brand
        """
        if self.context['request'].method == 'POST':
            pass
            # user_brands = Brand.objects.filter(ac_manager=self.context['request'].user)
            # if obj['license'] not in user_brands and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
            #     raise serializers.ValidationError(
            #         "You can only add/update license related to your brand only!")
        return obj

    def update(self, instance, validated_data):
        if validated_data.get('status') == 'completed':
            try:
                profile = LicenseProfile.objects.get(license=instance.id)
                notify_admins_on_profile_registration(
                    profile.license.created_by.email, profile.name,instance)
                #Create zoho books customer
                if profile.license.created_by.membership_type == "personal":
                    create_customer_in_books(profile.license.id, is_update=False, is_single_user=True, params={})
                elif profile.license.created_by.membership_type == "business":
                    if profile.license.brand:
                        create_customer_in_books(profile.license.brand.id, is_update=False, is_single_user=False, params={})
                    else:
                        create_customer_in_books(id=None,is_update=False, is_single_user=False, params={})
                #insert or update vendors/accounts
                insert_or_update_vendor_accounts(profile,instance)
            except Exception as e:
                print(e)
        user = super().update(instance, validated_data)
        return user

    class Meta:
        model = License
        fields = ('__all__')
        read_only_fields = ['approved_on', 'approved_by',
                            'uploaded_sellers_permit_to', 'uploaded_license_to']


class ProfileContactSerializer(serializers.ModelSerializer):
    """
    This defines ProfileContactSerializer
    """
    class Meta:
        model = ProfileContact
        fields = ('__all__')


class CultivationOverviewSerializer(serializers.ModelSerializer):
    """
    This defines CultivationOverviewSerializer
    """
    class Meta:
        model = CultivationOverview
        fields = ('__all__')


class LicenseProfileSerializer(serializers.ModelSerializer):
    """
    This defines LicenseProfileSerializer
    """

    def validate(self, attrs):
        """
        Object level validation.after brand Associated properly associate brand with license
        """
        if self.context['request'].method == 'PATCH':
            profile = LicenseProfile.objects.filter(
                license_id=self.context['request'].parser_context["kwargs"]["pk"])
            if self.context['request'].data.get('brand_association'):
                user_brands = Brand.objects.filter(
                    ac_manager=self.context['request'].user).values_list('id', flat=True)
                if self.context['request'].data.get('brand_association') not in user_brands:
                    raise serializers.ValidationError(
                        "You can only associate/update license related to your brand only!")
                license_obj = License.objects.filter(
                    id=self.context['request'].parser_context["kwargs"]["pk"])
                if license_obj:
                    license_obj[0].brand_id = attrs.get('brand_association')
                    license_obj[0].save()
        return attrs

    def update(self, instance, validated_data):
        """
        Update for licenseprofile
        """
        user = super().update(instance, validated_data)
        return user

    class Meta:
        model = LicenseProfile
        fields = ('__all__')


class FinancialOverviewSerializer(serializers.ModelSerializer):
    """
    This defines FinancialOverviewSerializer
    """
    class Meta:
        model = FinancialOverview
        fields = ('__all__')


class CropOverviewSerializer(serializers.ModelSerializer):
    """
    This defines CropOverviewSerializer
    """
    class Meta:
        model = CropOverview
        fields = ('__all__')


class ProgramOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer
    """
    class Meta:
        model = ProgramOverview
        fields = ('__all__')


class ProfileReportSerializer(serializers.ModelSerializer):
    """
    This defines ProfileReport serializer
    """

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to upload reports related to his VendorProfile.
        """
        if self.context['request'].method == 'POST':
            if not (obj['user'] == self.context['request'].user):
                raise serializers.ValidationError(
                    "You are not allowed to create report with another user!")

        return obj

    class Meta:
        model = ProfileReport
        fields = ('__all__')


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    name = serializers.CharField(read_only=True)
    license = serializers.CharField(write_only=True)

    def create(self, validated_data):
        key = 'uploaded_sellers_permit_to' if 'seller-permit' in validated_data[
            'file'].name else 'uploaded_license_to'
        upload_file('111282192684', validated_data['file'].temporary_file_path(),
                    validated_data['file'].name, validated_data['license'], key)
        return {'name': validated_data['file'].name}


class InviteUserRelatedLicenceField(serializers.RelatedField):
    queryset = License.objects.all()

    def to_representation(self, obj):
        return obj.pk

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=data)
        except License.DoesNotExist:
            raise serializers.ValidationError(
            f'License id {data} does not exist or you do not have access.'
            )

    def display_value(self, obj):
        return f'{obj.license_number} | {obj.legal_business_name}'

    def get_queryset(self):
        queryset = super().get_queryset()
        # queryset = queryset.filter(created_by=self.context['request'].user)
        return queryset


class InviteUserSerializer(serializers.Serializer):
    """
    This defines Brand serializer.
    """
    
    full_name = serializers.CharField(max_length=200)
    phone = PhoneNumberField(max_length=15)
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=LicenseRole.ROLE_CHOICES)
    licenses = InviteUserRelatedLicenceField(many=True,)

    def validate_licenses(self, value):
        """
        Check that license is selected.
        """
        if not value:
            raise serializers.ValidationError("At leat one License must be selected.")
        return value

    def validate_phone(self, value):
        """
        nonfield validation.
        """
        try:
            user = User.objects.get(phone=self.initial_data['phone'])
            if user.email != self.initial_data['email']:
                raise serializers.ValidationError("Phone number already in usefor another account.")
        except User.DoesNotExist:
            pass
        return value
