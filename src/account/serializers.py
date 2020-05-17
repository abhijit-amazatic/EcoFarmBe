"""
Serializer to validate Account related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Account,AccountLicense, AccountBasicProfile, AccountContactInfo, )
from user.models import User

class AccountSerializer(serializers.ModelSerializer):
    """
    This defines Account serializer.
    """
    def validate(self, data):
        if self.partial:
            pass
        return data
        
    class Meta:
        model = Account
        fields = ('__all__')

class AccountCreateSerializer(serializers.ModelSerializer):
    """
    This defines Account creation serializer and related validation
    """
    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to create Account only with self foreign key.
        """
        if not (obj['ac_manager'] == self.context['request'].user) and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
            raise serializers.ValidationError(
                "You are not allowed to create Account with another user!")

        return obj

    class Meta:
        model = Account
        fields = ('__all__')

class AccountLicenseSerializer(serializers.ModelSerializer):
    """
    This defines Account License Serializer.
    """

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to upload license related to his Account.
        """
        if self.context['request'].method == 'POST':
            accounts = Account.objects.filter(account__ac_manager=self.context['request'].user)
            if obj['account'] not in accounts and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
                raise serializers.ValidationError(
                    "You can only add/update license related to your Account only!")            
        return obj
        
    class Meta:
        model = AccountLicense
        fields = ('__all__')
        

class AccountBasicProfileSerializer(serializers.ModelSerializer):
    """
    This defines AccountBasicProfile serializer.
    """     
    class Meta:
        model = AccountBasicProfile
        fields = ('__all__')

class AccountContactInfoSerializer(serializers.ModelSerializer):
    """
    This defines AccountContactInfo serializer.
    """ 
    class Meta:
        model = AccountContactInfo
        fields = ('__all__')
