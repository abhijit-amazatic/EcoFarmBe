"""
Admin related customization.
"""
import json
from django.contrib import admin
from django import forms
from core.mailer import mail, mail_send
from django.conf import settings
from django.contrib.postgres import fields
from django.db import transaction
from django_json_widget.widgets import JSONEditorWidget
import nested_admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from user.models import (User, MemberCategory,)
from django.contrib import messages
from django.utils import timezone
from .models import (Vendor,VendorProfile,VendorUser,ProfileContact, ProfileOverview, FinancialOverview, ProcessingOverview, ProgramOverview, License,VendorCategory, )
from core.utility import send_async_approval_mail
from integration.crm import (insert_vendors, )


class VendorProfileForm(forms.ModelForm):

    class Meta:
        model = VendorProfile
        fields = '__all__'

    def clean(self):
        if self.changed_data:
            if 'status' in self.changed_data and self.cleaned_data.get('status') == 'approved':
                vendor_obj = Vendor.objects.filter(id=self.instance.vendor.id)
                if vendor_obj:
                    ac_manager = vendor_obj[0].ac_manager.email
                    mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Profile Approved.", ac_manager)
                

class InlineVendorUserAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    extra = 0
    model = VendorUser
    fields = ('user', 'role', )
    raw_id_fields = ('user', )
    autocomplete_lookup_fields = {
        'fk': ['user', ],
    }

class ProfileContactForm(forms.ModelForm):
    class Meta:
        model = ProfileContact
        fields = '__all__'
        widgets = {
            'profile_contact_details': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
    
        
class InlineVendorProfileContactAdmin(nested_admin.NestedStackedInline):#(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProfileContact model
    """
    extra = 0
    model = ProfileContact
    readonly_fields = ('is_draft',)
    can_delete = False
    form = ProfileContactForm    
    
class ProfileOverviewForm(forms.ModelForm):
    class Meta:
        model = ProfileOverview
        fields = '__all__'
        widgets = {
            'profile_overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
    
class InlineProfileOverviewAdmin(nested_admin.NestedStackedInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProfileOverview model
    """
    extra = 0
    model = ProfileOverview
    readonly_fields = ('is_draft',)
    can_delete = False
    form = ProfileOverviewForm    

class FinancialOverviewForm(forms.ModelForm):
    class Meta:
        model = FinancialOverview
        fields = '__all__'
        widgets = {
            'financial_details': JSONEditorWidget(options={'modes':['code','text'],'search': True},height='80%'),
        }
        
class InlineFinancialOverviewAdmin(nested_admin.NestedStackedInline):#(admin.TabularInline):
    """
    Configuring field admin view for FinancialOverview model
    """
    extra = 0
    model = FinancialOverview
    can_delete = False
    readonly_fields = ('is_draft',)
    form = FinancialOverviewForm

class ProcessingOverviewForm(forms.ModelForm):
    class Meta:
        model = ProcessingOverview
        fields = '__all__'
        widgets = {
            'processing_config': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
        
class InlineProcessingOverviewAdmin(nested_admin.NestedStackedInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProcessingOverview model
    """
    extra = 0
    model = ProcessingOverview
    readonly_fields = ('is_draft',)
    can_delete = False
    form = ProcessingOverviewForm

class ProgramOverviewForm(forms.ModelForm):
    class Meta:
        model = ProgramOverview
        fields = '__all__'
        widgets = {
            'program_details': JSONEditorWidget(options={'modes':['code','text'],'search': True}, height='50%'),
        }
        
class InlineProgramOverviewAdmin(nested_admin.NestedStackedInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProgramOverview model
    """
    extra = 0
    model = ProgramOverview
    readonly_fields = ('is_draft',)
    can_delete = False
    form = ProgramOverviewForm

class InlineLicenseAdmin(nested_admin.NestedStackedInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProgramOverview model
    """
    extra = 0
    model = License
    readonly_fields = ('license_number',)
    can_delete = False    
    
    
class InlineVendorProfileAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for VendorProfile model
    """
    extra = 0
    model = VendorProfile
    readonly_fields = ('vendor', 'profile_type','is_updated_in_crm','zoho_crm_id', 'is_draft', 'step', 'number_of_legal_entities','created_on','updated_on')
    form = VendorProfileForm
    can_delete = False    
    inlines = [InlineVendorProfileContactAdmin,InlineProfileOverviewAdmin,InlineFinancialOverviewAdmin,InlineProcessingOverviewAdmin,InlineProgramOverviewAdmin,InlineLicenseAdmin,]
    

class MyVendorAdmin(nested_admin.NestedModelAdmin):#(admin.ModelAdmin):
    """
    Configuring Vendors
    """
    inlines = [InlineVendorProfileAdmin, InlineVendorUserAdmin,]
    extra = 0
    model = Vendor
    readonly_fields = ('ac_manager','vendor_category','created_on','updated_on')
    list_display = ('profile_name','ac_manager','vendor_category',)
    search_fields = ('ac_manager__email','vendor_category',)
    list_filter = (
        ('created_on', DateRangeFilter), ('updated_on', DateRangeFilter),
    )
         

class VendorProfileUpdatedForm(forms.ModelForm):

    class Meta:
        model = VendorProfile
        fields = '__all__'

    # def clean(self):
    #     if self.changed_data:
    #         if 'status' in self.changed_data and self.cleaned_data.get('status') == 'approved' and self.instance.vendor.vendor_category == 'cultivation':
    #             send_async_approval_mail(self.instance.vendor.id)


def get_user_data(request):
    """
    return user info dict.
    """
    return {'id':request.user.id,
            'email':request.user.email,
            'first_name':request.user.first_name,
            'last_name':request.user.last_name}

def approve_vendor_profile(modeladmin, request, queryset):
    """
    Function for bulk profile approval.
    """
    for profile in queryset:
        if profile.vendor.vendor_category == 'cultivation' and profile.status == 'approved':
            pass
        elif profile.vendor.vendor_category == 'cultivation':
            profile.status ='approved'
            profile.approved_on  = timezone.now()
            profile.approved_by = get_user_data(request)
            profile.save()
            insert_vendors.delay(id=profile.id)
            send_async_approval_mail.delay(profile.vendor.id)
                
    messages.success(request,'Vendor Profiles Approved!')    
approve_vendor_profile.short_description = 'Approve Selected Vendor Profiles'


class MyVendorProfileAdmin(nested_admin.NestedModelAdmin):#(admin.ModelAdmin):
    """
    Configuring Vendor Profile
    """
    def approved_by_member(self, obj):
        return obj.approved_by.get('email',"N/A")
    
    def vendor_category(self, obj):
        return obj.vendor.vendor_category

    def ac_manager(self, obj):
        return obj.vendor.ac_manager

    def get_search_results(self, request, queryset, search_term):
        """
        Default and custom search filter for farm names.
        """
        queryset, use_distinct = super(MyVendorProfileAdmin, self).get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.select_related('profile_contact').filter(profile_contact__profile_contact_details__contains={'farm_name':search_term})
        return queryset, use_distinct
    
    inlines = [InlineVendorProfileContactAdmin,InlineProfileOverviewAdmin,InlineFinancialOverviewAdmin,InlineProcessingOverviewAdmin,InlineProgramOverviewAdmin,InlineLicenseAdmin,]
    form = VendorProfileUpdatedForm
    extra = 0
    model = VendorProfile
    list_display = ('profile_name','status','vendor_category','approved_on','approved_by_member','ac_manager','created_on','updated_on',)
    list_select_related = ['vendor__ac_manager']
    search_fields = ('profile_type','vendor__vendor_category','vendor__ac_manager__email','status')
    readonly_fields = ('vendor','vendor_id', 'profile_type','is_updated_in_crm','zoho_crm_id', 'is_draft', 'step', 'number_of_legal_entities','created_on','updated_on', 'number_of_licenses','approved_on','approved_by',)
    list_filter = (
        ('created_on', DateRangeFilter), ('updated_on', DateRangeFilter),('approved_on',DateRangeFilter ),'status',
    )
    ordering = ('status','approved_on','created_on','updated_on')
    actions = [approve_vendor_profile, ] 
    list_per_page = 50

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'approved' and obj.vendor.vendor_category == 'cultivation':
            send_async_approval_mail(obj.vendor.id)
            insert_vendors.delay(id=obj.id)
            obj.approved_on  = timezone.now()
            obj.approved_by = get_user_data(request)
            obj.save()
        super().save_model(request, obj, form, change)
        
    

class VendorCategoryAdmin(admin.ModelAdmin):
    """
    VendorAdmin
    """
    #search_fields = ('',)
        
#admin.site.register(Vendor,MyVendorAdmin)
admin.site.register(VendorProfile,MyVendorProfileAdmin)
admin.site.register(VendorCategory, VendorCategoryAdmin)  
