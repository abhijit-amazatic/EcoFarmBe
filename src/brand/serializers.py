"""
Serializer to validate brand related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Brand,License,LicenseUser,ProfileContact,LicenseProfile,CultivationOverview,ProgramOverview,FinancialOverview,CropOverview)
from user.models import User
from core.utility import (notify_farm_user, notify_admins_on_vendors_registration, notify_admins_on_profile_registration)

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
    This defines VendorProfile serializer.
    """
    farm = serializers.SerializerMethodField(read_only=True)

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to create VendorProfile only with respective vendor
        """
        if self.context['request'].method == 'POST':
            #user_vendors = Vendor.objects.filter(ac_manager=self.context['request'].user)
            user_vendors = Vendor.objects.filter(vendor_roles__user=self.context['request'].user)
            if obj['vendor'] not in user_vendors and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
                raise serializers.ValidationError(
                    "You can only add/update vendorprofiles related to your vendors only!")
        return obj

    def update(self, instance, validated_data):
        profile = VendorProfile.objects.select_related('vendor').get(id=instance.id)
        if profile.vendor.vendor_category == 'cultivation' and validated_data.get('status') == 'completed':
            try:
                insert_vendors.delay(id=instance.id,is_update=True)
                profile_contact = ProfileContact.objects.get(vendor_profile=instance.id)
                notify_admins_on_profile_registration(profile.vendor.ac_manager.email, profile_contact.profile_contact_details['farm_name'])
            except Exception as e:
                print(e)
        user = super().update(instance, validated_data)
        return user

    def get_farm(self, obj):
        """
        Return respective farm names.
        """
        return obj.profile_name()

    class Meta:
        model = VendorProfile
        fields = ('__all__')
        read_only_fields = ['approved_on', 'approved_by']       
