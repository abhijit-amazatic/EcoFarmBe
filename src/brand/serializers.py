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
            raise serializers.ValidationError("You are not allowed to create brand with another user!")
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
            user_brands = Brand.objects.filter(ac_manager=self.context['request'].user)
            if obj['license'] not in user_brands and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
                raise serializers.ValidationError(
                    "You can only add/update license related to your brand only!")
        return obj

    def update(self, instance, validated_data):
        profile = License.objects.select_related('brand').get(id=instance.id)
        if validated_data.get('status') == 'completed':
            try:
                pass
            except Exception as e:
                print(e)
        user = super().update(instance, validated_data)
        return usero

    class Meta:
        model = License
        fields = ('__all__')
        read_only_fields = ['approved_on', 'approved_by']       


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
    class Meta:
        model  = LicenseProfile
        fields = ('__all__')
        
class FinancialOverviewSerializer(serializers.ModelSerializer):
    """
    This defines FinancialOverviewSerializer
    """
    class Meta:
        model  = FinancialOverview
        fields = ('__all__')

class CropOverviewSerializer(serializers.ModelSerializer):
    """
    This defines CropOverviewSerializer
    """
    class Meta:
        model  = CropOverview
        fields = ('__all__')


class ProgramOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer
    """
    class Meta:
        model  = ProgramOverview
        fields = ('__all__')                           
        
