"""
Serializer to validate vendor related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import Vendor, VendorProfile

class VendorSerializer(serializers.ModelSerializer):
    """
    This defines Vendor serializer.
    """
    def validate(self, data):
        if self.partial:
            pass
        return data
        
    class Meta:
        model = Vendor
        fields = ('__all__')
             

class VendorCreateSerializer(serializers.ModelSerializer):
    """
    This defines Vendor creation serializer and related validation
    """
    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to create Vendor only with self foreign key.
        """
        if not (obj['ac_manager'] == self.context['request'].user) and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
            raise serializers.ValidationError(
                "You are not allowed to create Vendor with another user!")

        return obj

    class Meta:
        model = Vendor
        fields = ('__all__')

        
