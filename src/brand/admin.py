"""
Admin related customization.
"""

import json
from django.contrib import admin
from django.db import models
from django import forms
from core.mailer import mail, mail_send
from django.conf import settings
from django.contrib.postgres import fields
from django.contrib.admin import widgets
from django.db import transaction
from django_json_widget.widgets import JSONEditorWidget
import nested_admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from user.models import (User,)
from django.contrib import messages
from django.utils import timezone
from django_reverse_admin import ReverseModelAdmin
from .models import (Organization, Brand,License,LicenseUser,ProfileContact,LicenseProfile,CultivationOverview,ProgramOverview,FinancialOverview,CropOverview, ProfileCategory)
from .models import (LicenseRole,)
from core.utility import (send_async_approval_mail,add_users_to_system_and_license,get_profile_type,)
from integration.box import (delete_file,)


class LicenseUpdatedForm(forms.ModelForm):

    class Meta:
        model = License
        fields = '__all__'

    def clean(self):
        if self.changed_data:
            if 'status' in self.changed_data and self.cleaned_data.get('status') == 'approved':
                license_obj = License.objects.filter(id=self.instance.id)
                if license_obj:
                    ac_manager = license_obj[0].created_by.email
                    profile_type = get_profile_type(license_obj[0])
                    mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login', 'profile_type': profile_type,'legal_business_name': license_obj[0].legal_business_name},"Your %s profile has been approved."% profile_type, ac_manager)
                    

def approve_license_profile(modeladmin, request, queryset):
    """
    Function for bulk profile approval.
    """
    for profile in queryset:
        if profile.status != 'approved':
            profile.status ='approved'
            profile.save()
            license_profile = LicenseProfile.objects.filter(license=profile)
            if license_profile:
                license_profile[0].approved_on  = timezone.now()
                license_profile[0].approved_by = get_user_data(request)
                license_profile[0].save()
            send_async_approval_mail.delay(profile.id)
            if hasattr(profile, 'profile_contact'):
                add_users_to_system_and_license.delay(profile.profile_contact.id,profile.id)
                
    messages.success(request,'License Profiles Approved!')    
approve_license_profile.short_description = 'Approve Selected License Profiles'



def get_obj_file_ids(obj):
    """
    Extract box file ids
    """
    box_file_ids = []
    #doc_field = ['uploaded_license_to','uploaded_sellers_permit_to']
    links = License.objects.filter(id=obj.id).values('uploaded_license_to','uploaded_sellers_permit_to')
    to_be_removed = [ v for k, v in links[0].items() if v is not None]
    try:
        if links:
            for doc in to_be_removed:
                if '?id=' in doc:
                    box_id = doc.split('?id=')[1]
                else:
                    box_id = doc
                if box_id:     
                    box_file_ids.append(box_id)
            return box_file_ids
    except Exception as e:
        print('exception',e)
        
            

def delete_model(modeladmin, request, queryset):
    for obj in queryset:
        file_ids = get_obj_file_ids(obj)
        if file_ids:
            for file_id in file_ids:
                print('FileID to delete from box:',file_id)
                delete_file(file_id)
        obj.delete()
delete_model.short_description = "Delete selected License Profile and it's box files"


class ProfileContactForm(forms.ModelForm):
    class Meta:
        model = ProfileContact
        fields = '__all__'
        widgets = {
            'profile_contact_details': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
        
class InlineLicenseProfileContactAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    extra = 0
    model = ProfileContact
    readonly_fields = ('is_draft',)
    can_delete = False
    form = ProfileContactForm


class CultivationForm(forms.ModelForm):
    class Meta:
        model = CultivationOverview
        fields = '__all__'
        widgets = {
            'overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
        

class InlineCultivationOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for CultivationOverview.
    """
    extra = 0
    model = CultivationOverview
    readonly_fields = ('is_draft','overview',)
    can_delete = False
    form = CultivationForm

class FinancialForm(forms.ModelForm):
    class Meta:
        model = FinancialOverview
        fields = '__all__'
        widgets = {
            'overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }    

class InlineFinancialOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for FinancialOverview model.
    """
    extra = 0
    model = FinancialOverview
    can_delete = False
    readonly_fields = ('is_draft','overview',)
    form = FinancialForm

class CropForm(forms.ModelForm):
    class Meta:
        model = CropOverview
        fields = '__all__'
        widgets = {
            'overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }        

class InlineCropOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for InlineCropOverview model.
    """
    extra = 0
    model = CropOverview
    can_delete = False
    readonly_fields = ('is_draft','overview',)
    form = CropForm
    

class InlineProgramOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for InlineProgramOverviewAdmin  model
    """
    extra = 0
    model = ProgramOverview
    can_delete = False
    readonly_fields = ('is_draft',)
 
class InlineLicenseProfileAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for InlineLicenseProfile  model
    """
    extra = 0
    model = LicenseProfile
    can_delete = False
    readonly_fields = ('is_draft',)   
    
class InlineLicenseUserAdmin(nested_admin.NestedTabularInline):
    extra = 0
    model = LicenseUser

def get_user_data(request):
    """
    return user info dict.
    """
    return {'id':request.user.id,
            'email':request.user.email,
            'first_name':request.user.first_name,
            'last_name':request.user.last_name}


class MyLicenseAdmin(nested_admin.NestedModelAdmin):
    """
    Configuring License
    """
    def approved_on(self, obj):
        return obj.license_profile.approved_on

    def name(self, obj):
        return obj.license_profile.name
    
    def approved_by(self, obj):
        if obj.license_profile.approved_by:
            return obj.license_profile.approved_by.get('email',"N/A")
        return "N/A"
        

    def get_search_results(self, request, queryset, search_term):
        """
        Default and custom search filter for farm names.
        """
        queryset, use_distinct = super(MyLicenseAdmin, self).get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.select_related('license_profile').filter(license_profile__name__contains={'name':search_term})
        return queryset, use_distinct
    
    inlines = [InlineLicenseProfileAdmin,InlineLicenseProfileContactAdmin,InlineCultivationOverviewAdmin,InlineFinancialOverviewAdmin,InlineCropOverviewAdmin,InlineProgramOverviewAdmin, InlineLicenseUserAdmin]
    form = LicenseUpdatedForm
    extra = 0
    model = License
    list_display = ('name','brand','legal_business_name','status','profile_category','approved_on','approved_by','created_by','created_on','updated_on',)
    list_select_related = ['brand__ac_manager']
    search_fields = ('brand__brand_name','brand__ac_manager__email','status')
    readonly_fields = ('created_on','updated_on','created_by',)
    list_filter = (
        ('created_on', DateRangeFilter), ('updated_on', DateRangeFilter),'status',
    )
    ordering = ('-created_on','legal_business_name','status','updated_on',)
    actions = [approve_license_profile, delete_model, ] 
    list_per_page = 50

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'approved':
            send_async_approval_mail(obj.id)
            license_profile = LicenseProfile.objects.filter(license=obj)
            if license_profile:
                license_profile[0].approved_on  = timezone.now()
                license_profile[0].approved_by = get_user_data(request)
                license_profile[0].save()
            if hasattr(obj, 'profile_contact'):    
                add_users_to_system_and_license.delay(obj.profile_contact.id,obj.id)
            
        super().save_model(request, obj, form, change)

class OrganizationAdmin(admin.ModelAdmin):
    """
    Configuring brand
    """
    model = Organization
    list_display = ('name', 'created_by', 'created_on', 'updated_on',)
    search_fields = ('name', 'created_by',)
    list_filter = (
        ('created_on', DateRangeFilter),
        ('updated_on', DateRangeFilter),
    )
    ordering = ('-created_on', 'updated_on',)

        
class MyBrandAdmin(admin.ModelAdmin):
    """
    Configuring brand
    """    
    extra = 0
    model = Brand
    #inlines = [InlineAccountLicenseAdmin,InlineAccountBasicProfileAdmin,InlineAccountContactInfoAdmin, InlineAccountUserAdmin]
    list_display = ('brand_name','ac_manager','appellation','created_on', 'updated_on',)
    search_fields = ('brand_name', 'ac_manager', 'appellation')
    list_filter = (
        ('created_on', DateRangeFilter),('updated_on',DateRangeFilter ),
    )
    ordering = ('-created_on','updated_on',)

    
class ProfileCategoryAdmin(admin.ModelAdmin):
    """
    ProfileCategoryAdmin
    """
    #search_fields = ('',)
    

class LicenseRoleAdmin(admin.ModelAdmin):
    """
    ProfileCategoryAdmin
    """
    formfield_overrides = {
        models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
    }



admin.site.register(LicenseRole,LicenseRoleAdmin)
admin.site.register(Organization,OrganizationAdmin)
admin.site.register(Brand,MyBrandAdmin)
admin.site.register(License,MyLicenseAdmin)
admin.site.register(ProfileCategory, ProfileCategoryAdmin)

