"""
Serializer to validate Account related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Account,AccountLicense, AccountBasicProfile, AccountContactInfo, )
from core.utility import (notify_admins_on_accounts_registration,)
from integration.crm import (insert_accounts, )
from user.models import User

class AccountSerializer(serializers.ModelSerializer):
    """
    This defines Account serializer.
    """
    def validate(self, data):
        if self.partial:
            pass
        return data

    def update(self, instance, validated_data):
        if validated_data.get('status') == 'completed':
            try:
                insert_accounts.delay(id=instance.id,is_update=True)
                notify_admins_on_accounts_registration(instance.ac_manager.email,instance.account_profile.company_name)
            except Exception as e:
                print(e)
        user = super().update(instance, validated_data)
        return user
        
    class Meta:
        model = Account
        fields = ('__all__')
        read_only_fields = ['approved_on','approved_by']

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
        read_only_fields = ['approved_on','approved_by']

class AccountLicenseSerializer(serializers.ModelSerializer):
    """
    This defines Account License Serializer.
    """

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to upload license related to his Account.
        """
        if self.context['request'].method == 'POST':
            accounts = Account.objects.filter(ac_manager=self.context['request'].user)
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
