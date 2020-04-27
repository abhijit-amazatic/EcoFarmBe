"""
Serializer to validate vendor related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Vendor, VendorProfile, ProfileContact, ProfileOverview, FinancialOverview, ProcessingOverview,  License, ProgramOverview, VendorUser)

from user.models import User
from core.utility import (notify_farm_user, notify_admins_on_vendors_registration)


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

        
class ConfigEmployeeSerializer(serializers.Serializer):
    """
    Employee data for cultivator.
    """
    phone = serializers.CharField(required=False)
    roles = serializers.ListField(required=True)
    employee_name = serializers.CharField(required=True)
    employee_email = serializers.EmailField(required=True)

    
class CultivatorFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator.
    """
    farm_name = serializers.CharField(required=True)
    primary_county = serializers.CharField(required=True)
    region = serializers.CharField(required=True)
    appellation = serializers.CharField(required=True)
    ethics_and_certifications = serializers.ListField(required=True)
    other_distributors = serializers.CharField(required=True)
    transportation = serializers.ListField(required=True)
    packaged_flower_line = serializers.CharField(required=True)
    interested_in_co_branding = serializers.CharField(required=True)
    marketing_material = serializers.CharField(required=True)
    featured_on_our_site = serializers.CharField(required=True)
    company_email = serializers.CharField(required=True)
    company_phone = serializers.CharField(required=True)
    website = serializers.CharField(required=True)
    instagram = serializers.CharField(required=True)
    facebook = serializers.CharField(required=True)
    linkedin = serializers.CharField(required=True)
    twitter = serializers.CharField(required=True)
    no_of_employees = serializers.CharField(required=True)
    employees = ConfigEmployeeSerializer(required=True, many=True)
    #employees = serializers.ListField(child=serializers.DictField(), required=False)
    

class ProfileContactSerializer(serializers.ModelSerializer):
    """
    This defines ProfileContactSerializer.
    """
    profile_contact_details = serializers.JSONField(required=True)
    is_draft = serializers.BooleanField(required=True)
    
    def validate(self, attrs):
        """
        Object level validation
        catch vendor like this 'profile.vendor'.
        fields are different for different vendors
        """    
        #if self.partial:
        if self.context['request'].method == 'PATCH' and not attrs.get('is_draft'):
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivator':
                profile_data = attrs.get('profile_contact_details')
                if profile_data:
                    serializer = CultivatorFieldsSerializer(data=profile_data)
                    serializer.is_valid(raise_exception=True)   
            
        return attrs

    def create_and_notify_employee(self, profile, validated_data):
        """
        Generic for create and update as if is_draft is 'true' we need to bypass. validations
        """
        employee_data = validated_data.get('profile_contact_details')['employees']
        new_users = []
        for employee in employee_data:
            obj, created = User.objects.get_or_create(email=employee['employee_email'],
                                                      defaults={'email':employee['employee_email'],
                                                                'username':employee['employee_name'],
                                                                'phone':employee['phone'],
                                                                'is_verified':True,
                                                                'existing_member':True})
            if created:
                new_users.append(obj)
                if not VendorUser.objects.filter(user_id=obj.id, vendor_id=profile.vendor.id).exists():
                    VendorUser(user_id=obj.id, vendor_id=profile.vendor.id,role=','.join(employee['roles'])).save()
                    notify_farm_user(obj.email, validated_data.get('profile_contact_details')['farm_name'])
                    notify_admins_on_vendors_registration(obj.email,validated_data.get('profile_contact_details')['farm_name'] )    
                        

        
    def create(self,validated_data):
        """
        When object is created add custom method here.
        """
        profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
        if profile.vendor.vendor_category == 'cultivator' and not validated_data.get('is_draft'):
            self.create_and_notify_employee(profile,validated_data)
        else:
            pass #this is added for further conditions
            
        profile = super().create(validated_data)
        #profie.something
        #profile.save()
        return profile


    def update(self, instance, validated_data):
        profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
        if profile.vendor.vendor_category == 'cultivator' and not validated_data.get('is_draft'):
            self.create_and_notify_employee(profile,validated_data)
        user = super().update(instance, validated_data)
        return user
         
    class Meta:
        model = ProfileContact
        fields = ('__all__')


class OverviewFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator profile_overview.
    """
    lighting_type = serializers.ListField(required=True)
    type_of_nutrients = serializers.CharField(required=True)
    issues_with_failed_lab_tests = serializers.CharField(required=True)
    lab_test_issues = serializers.CharField(required=True)
    process_on_site = serializers.CharField(required=True)
    interested_in_growing_genetics = serializers.CharField(required=True)
    avg_yield_pr_sq_ft = serializers.CharField(required=True)
    know_yield_per_sq_ft = serializers.CharField(required=True)
    yield_per_plant = serializers.CharField(required=True)
    know_yield_per_plant = serializers.CharField(required=True)
    plants_cultivate_per_cycle = serializers.CharField(required=True)
    annual_untrimmed_yield = serializers.CharField(required=True)
    

    
class ProfileOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProfileOverviewSerializer
    """
    profile_overview = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH':
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivator':
                profile_data = attrs.get('profile_overview')
                if profile_data:
                    serializer = OverviewFieldsSerializer(data=profile_data)
                    serializer.is_valid(raise_exception=True)   
            
        return attrs
    
    class Meta:
        model = ProfileOverview
        fields = ('__all__')


class FinanceFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator finance overview.
    """
    annual_revenue_2019 = serializers.CharField(required=True)
    projected_2020_revenue = serializers.CharField(required=True)
    target_profit_margin = serializers.CharField(required=True)
    yearly_budget = serializers.CharField(required=True)
    know_cost_per_lbs = serializers.CharField(required=True)
    cost_per_lbs = serializers.CharField(required=True)
    know_cost_per_sqf = serializers.CharField(required=True)
    cost_per_sqf = serializers.CharField(required=True)
    avg_target_price = serializers.CharField(required=True)
    small_target_price = serializers.CharField(required=True)
    trim_target_price = serializers.CharField(required=True)
    bucked_target_price = serializers.CharField(required=True)
    

    
class FinancialOverviewSerializer(serializers.ModelSerializer):
    """
    This defines FinancialOverviewSerializer.
    """
    financial_details = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH':
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivator':
                profile_data = attrs.get('financial_details')
                if profile_data:
                    serializer = FinanceFieldsSerializer(data=profile_data)
                    serializer.is_valid(raise_exception=True)   
            
        return attrs
    
    class Meta:
        model = FinancialOverview
        fields = ('__all__')


class ConfigCultivarsSerializer(serializers.Serializer):
    """
    cultivars data for processing config
    """
    harvest_date = serializers.CharField(required=True)
    cultivar_names = serializers.ListField(required=True)
   
        
class ProcessingFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator processing overview.
    """
    no_of_harvest_per_year = serializers.IntegerField(required=True)
    no_of_harvest = serializers.IntegerField(required=True)
    outdoor_sqf = serializers.IntegerField(required=True)
    indoor_sqf = serializers.IntegerField(required=True)
    mixed_light_sqf = serializers.IntegerField(required=True)
    flower_yield_percentage = serializers.IntegerField(required=True)
    small_yield_percentage = serializers.IntegerField(required=True)
    trim_yield_percentage = serializers.IntegerField(required=True)
    cultivars = ConfigCultivarsSerializer(required=True, many=True)
     
        
class ProcessingOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProcessingOverviewSerializer.
    """
    processing_config  = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH':
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivator':
                profile_data = attrs.get('processing_config')
                if profile_data:
                    serializer = ProcessingFieldsSerializer(data=profile_data)
                    serializer.is_valid(raise_exception=True)   
            
        return attrs
    
    class Meta:
        model = ProcessingOverview
        fields = ('__all__')


class ProgramFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator program.
    """
    program_name = serializers.CharField(required=True)
    
    
class ProgramOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProgramOverviewSerializer.
    """
    program_details = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH':
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivator':
                profile_data = attrs.get('program_details')
                if profile_data:
                    serializer = ProgramFieldsSerializer(data=profile_data)
                    serializer.is_valid(raise_exception=True)   
            
        return attrs
        
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

         
