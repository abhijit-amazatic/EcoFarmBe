"""
Serializer to validate vendor related modules.
"""

import requests
from django.conf import settings
from rest_framework import serializers
from .models import (Vendor, VendorProfile, ProfileContact, ProfileOverview, FinancialOverview, ProcessingOverview,  License, ProgramOverview, VendorUser)

from user.models import User
from core.utility import (notify_farm_user, notify_admins_on_vendors_registration, notify_admins_on_profile_registration)
from integration.crm import (insert_vendors, )

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

    def update(self, instance, validated_data):
        profile = VendorProfile.objects.select_related('vendor').get(id=instance.id)
        if profile.vendor.vendor_category == 'cultivation' and  validated_data.get('status') == 'completed':
            try:
                #insert_vendors.delay(id=instance.id)
                profile_contact = ProfileContact.objects.get(vendor_profile=instance.id)
                notify_admins_on_profile_registration(profile.vendor.ac_manager.email,profile_contact.profile_contact_details['farm_name'])
            except Exception as e:
                print(e)
        user = super().update(instance, validated_data)
        return user
    
    class Meta:
        model = VendorProfile
        fields = ('__all__')
        read_only_fields = ['approved_on','approved_by']


        
class ConfigEmployeeSerializer(serializers.Serializer):
    """
    Employee data for cultivator.
    """
    phone = serializers.CharField(required=False, allow_blank=True)
    roles = serializers.ListField(required=True,allow_empty=True)
    employee_name = serializers.CharField(required=True,allow_blank=True)
    employee_email = serializers.EmailField(required=True,allow_blank=True)

    
class CultivatorFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator.
    """
    farm_name = serializers.CharField(required=False,allow_blank=True)
    primary_county = serializers.CharField(required=False,allow_blank=True)
    region = serializers.CharField(required=False,allow_blank=True)
    appellation = serializers.CharField(required=False,allow_blank=True)
    ethics_and_certifications = serializers.ListField(required=False,allow_empty=True)
    other_distributors = serializers.CharField(required=False,allow_blank=True)
    transportation = serializers.ListField(required=False,allow_empty=True)
    packaged_flower_line = serializers.CharField(required=False,allow_blank=True)
    interested_in_co_branding = serializers.CharField(required=False,allow_blank=True)
    marketing_material = serializers.CharField(required=False,allow_blank=True)
    featured_on_our_site = serializers.CharField(required=False,allow_blank=True)
    company_email = serializers.CharField(required=False,allow_blank=True)
    company_phone = serializers.CharField(required=False,allow_blank=True)
    website = serializers.CharField(required=False,allow_blank=True)
    instagram = serializers.CharField(required=False,allow_blank=True)
    facebook = serializers.CharField(required=False,allow_blank=True)
    linkedin = serializers.CharField(required=False,allow_blank=True)
    twitter = serializers.CharField(required=False,allow_blank=True)
    no_of_employees = serializers.CharField(required=False,allow_blank=True)
    employees = ConfigEmployeeSerializer(required=False, many=True)
    billing_address = serializers.DictField(required=False, allow_empty=True) 
    mailing_address = serializers.DictField(required=False, allow_empty=True) 
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
            if profile.vendor.vendor_category == 'cultivation':
                profile_data = attrs.get('profile_contact_details')
                if profile_data:
                    serializer = CultivatorFieldsSerializer(data=profile_data)
                    serializer.is_valid(raise_exception=True)   
            
        return attrs

    def create_and_notify_employee(self, profile, validated_data):
        """
        Generic for create and update as if is_draft is 'true' we need to bypass. validations
        """
        employee_data = validated_data.get('profile_contact_details').get('employees',[])
        new_users = []
        if employee_data:
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
        if profile.vendor.vendor_category == 'cultivation' and not validated_data.get('is_draft'):
            self.create_and_notify_employee(profile,validated_data)
        else:
            pass #this is added for further conditions
            
        profile = super().create(validated_data)
        #profie.something
        #profile.save()
        return profile


    def update(self, instance, validated_data):
        profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
        if profile.vendor.vendor_category == 'cultivation' and not validated_data.get('is_draft'):
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
    type_of_nutrients = serializers.ListField(required=True,allow_empty=True)
    interested_in_growing_genetics = serializers.CharField(required=True)
    issues_with_failed_lab_tests = serializers.CharField(required=True)
    lab_test_issues = serializers.CharField(required=False, allow_blank=True)
    autoflower = serializers.BooleanField(required=False)
    full_season = serializers.BooleanField(required=False)
    outdoor_autoflower = serializers.DictField(required=False, allow_empty=True)
    outdoor_full_season = serializers.DictField(required=False, allow_empty=True)
    mixed_light = serializers.DictField(required=False, allow_empty=True)
    outdoor = serializers.DictField(required=False, allow_empty=True) 
    indoor = serializers.DictField(required=False, allow_empty=True)
    
    
class ProfileOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProfileOverviewSerializer
    """
    profile_overview = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH' and not attrs.get('is_draft'):
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivation':
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
    yearly_budget = serializers.CharField(required=True)
    outdoor_autoflower = serializers.DictField(required=False, allow_empty=True)
    outdoor_full_season = serializers.DictField(required=False, allow_empty=True)
    mixed_light = serializers.DictField(required=False, allow_empty=True)
    indoor = serializers.DictField(required=False, allow_empty=True)

    
class FinancialOverviewSerializer(serializers.ModelSerializer):
    """
    This defines FinancialOverviewSerializer.
    """
    financial_details = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH' and not attrs.get('is_draft'):
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivation':
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
    cultivation_type = serializers.CharField(required=False,allow_blank=True)
   
        
class ProcessingFieldsSerializer(serializers.Serializer):
    """
    JSON data for cultivator processing overview.
    """
    mixed_light = serializers.DictField(required=False, allow_empty=True)
    outdoor_autoflower = serializers.DictField(required=False, allow_empty=True)
    outdoor_full_season = serializers.DictField(required=False, allow_empty=True)
    indoor = serializers.DictField(required=False, allow_empty=True)
    process_on_site = serializers.CharField(required=True)
    #cultivars = ConfigCultivarsSerializer(required=True, many=True)
     
        
class ProcessingOverviewSerializer(serializers.ModelSerializer):
    """
    This defines ProcessingOverviewSerializer.
    """
    processing_config  = serializers.JSONField(required=True)

    def validate(self, attrs):
        """
        Object level validation.
        """    
        if self.context['request'].method == 'PATCH' and not attrs.get('is_draft'):
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivation':
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
        if self.context['request'].method == 'PATCH' and not attrs.get('is_draft'):
            profile = VendorProfile.objects.select_related('vendor').get(id=self.context['request'].parser_context["kwargs"]["pk"])
            if profile.vendor.vendor_category == 'cultivation':
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

         
