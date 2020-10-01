"""
Serializer to validate brand related modules.
"""

import requests
from django.conf import settings
from tempfile import TemporaryFile

from rest_framework import serializers
from .models import (Brand, License, LicenseUser, ProfileContact, LicenseProfile,
                     CultivationOverview, ProgramOverview, FinancialOverview, CropOverview, ProfileReport)
from user.models import User
from core.utility import (notify_admins_on_profile_registration,)
from integration.crm import (insert_vendors, insert_accounts,)
from integration.box import upload_file


class BrandSerializer(serializers.ModelSerializer):
    """
    This defines Brand serializer.
    """

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
                    profile.license.created_by.email, profile.name)
                if profile.license.profile_category == 'cultivation':
                    if instance.brand:
                        insert_vendors.delay(id=instance.brand.id)
                    else:
                        insert_vendors.delay(
                            id=instance.id, is_single_user=True)
                else:
                    if instance.brand:
                        insert_accounts.delay(id=instance.brand.id)
                    else:
                        insert_accounts.delay(
                            id=instance.id, is_single_user=True)
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
