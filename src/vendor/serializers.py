"""
Serializer to validate vendor related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Vendor, VendorProfile, ProfileContact, ProfileOverview, FinancialOverview, ProcessingOverview,  License, ProgramOverview)

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
        #vendor_roles__user
        if not (obj['ac_manager'] == self.context['request'].user) and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
            raise serializers.ValidationError(
                "You are not allowed to create Vendor with another user!")

        return obj

    class Meta:
        model = Vendor
        fields = ('__all__')

        
class VendorProfileSerializer(serializers.ModelSerializer):
    """
    This defines VendorProfile serializer.
    """

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
    
    class Meta:
        model = VendorProfile
        fields = ('__all__')



class ProfileContactSerializer(serializers.ModelSerializer):
    """
    This defines ProfileContactSerializer.
    """
    VALID_CULTIVATOR_KEYS = ['farm_name', 'primary_county', 'region', 'appellation', 'ethics_and_certifications', 'other_distributors', 'transportation', 'packaged_flower_line', 'interested_in_co_branding', 'marketing_material', 'featured_on_our_site', 'company_email', 'company_phone', 'website', 'instagram', 'facebook', 'linkedin', 'twitter', 'no_of_employees', 'employees', 'employee_name','employee_email', 'phone', 'roles']

    farm_name = serializers.CharField(required=False)
    primary_county = serializers.CharField(required=False)
    region = serializers.CharField(required=False)
    appellation = serializers.CharField(required=False)
    ethics_and_certifications = serializers.ListField(required=False)
    other_distributors = serializers.CharField(required=False)
    transportation = serializers.ListField(required=False)
    packaged_flower_line = serializers.CharField(required=False)
    interested_in_co_branding = serializers.CharField(required=False)
    marketing_material = serializers.CharField(required=False)
    featured_on_our_site = serializers.CharField(required=False)
    company_email = serializers.CharField(required=False)
    company_phone = serializers.CharField(required=False)
    website = serializers.CharField(required=False)
    instagram = serializers.CharField(required=False)
    facebook = serializers.CharField(required=False)
    linkedin = serializers.CharField(required=False)
    twitter = serializers.CharField(required=False)
    no_of_employees = serializers.CharField(required=False)
    employees = serializers.ListField(child=serializers.DictField(), required=False)
    
    def validate(self, attrs):
        """
        Object level validation
        catch vendor like this 'profile.vendor'
        """
        if self.partial:
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivator':
                #print('vendor--->', profile.vendor)
                attrs = super().validate(attrs)
                employees = attrs['employees']
                keys_list = []
                for item in some_config_vars:
                    keys_list.extend(list(item.keys()))
                    unwanted_keys = set(keys_list) - set(VALID_CULTIVATOR_KEYS)
                    if unwanted_keys:
                        raise serializers.ValidationError("Invalid key/keys.Please add valid keys!")
                    return attrs
                
        return attrs

    def update(self, instance, validated_data):
        # print('in update---> would return ob updated with id\n', instance.vendor_profile)
        # v = VendorProfile.objects.select_related('vendor').get(id=instance.vendor_profile.pk)
        # print('Vendor', v.vendor)
        #print(' validated_data--->',  validated_data)
        #if profile.vendor.vendor_category == 'cultivator':
         #   print('in update email here<><><>')
        #instance.email = validated_data.get('email', instance.email)
        #instance.save()
        return instance
        
    class Meta:
        model = ProfileContact
        fields = ('__all__')


class ProfileOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProfileOverviewSerializer
    """
       
    class Meta:
        model = ProfileOverview
        fields = ('__all__')


class FinancialOverviewSerializer(serializers.ModelSerializer):
    """
    This defines FinancialOverviewSerializer.
    """
        
    class Meta:
        model = FinancialOverview
        fields = ('__all__')

class ProcessingOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProcessingOverviewSerializer.
    """
        
    class Meta:
        model = ProcessingOverview
        fields = ('__all__')

class ProgramOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer.
    """
        
    class Meta:
        model = ProgramOverview
        fields = ('__all__')
        

class LicenseSerializer(serializers.ModelSerializer):
    """
    This defines License Serializer.
    """

    def validate(self, obj):
        """
        Object level validation.Normal user should allowed to upload license related to his VendorProfile.
        """
        if self.context['request'].method == 'POST':
            #vendor_profile = VendorProfile.objects.filter(vendor__ac_manager=self.context['request'].user)
            vendor_profiles = VendorProfile.objects.filter(vendor__vendor_roles__user=self.context['request'].user)
            if obj['vendor_profile'] not in vendor_profiles and not (self.context['request'].user.is_staff or self.context['request'].user.is_superuser):
                raise serializers.ValidationError(
                    "You can only add/update license related to your vendors/vendor profile only!")
            
        return obj
        
    class Meta:
        model = License
        fields = ('__all__')

         
