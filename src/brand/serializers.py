"""
Serializer to validate brand related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Brand,)
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
        # vendor_roles__user
        if not (obj['ac_manager'] == self.context['request'].user) and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
            raise serializers.ValidationError(
                "You are not allowed to create Vendor with another user!")

        return obj

    class Meta:
        model = Brand
        fields = ('__all__')
