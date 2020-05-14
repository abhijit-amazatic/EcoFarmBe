"""
Admin related customization.
"""
import json
from django.contrib import admin
from django import forms
from core.mailer import mail, mail_send
from django.conf import settings
from django.contrib.postgres import fields
from django_json_widget.widgets import JSONEditorWidget
import nested_admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from user.models import (User, MemberCategory,)
from .models import (Vendor,VendorProfile,VendorUser,ProfileContact, ProfileOverview, FinancialOverview, ProcessingOverview, ProgramOverview, License)
from django.contrib.admin import ModelAdmin, SimpleListFilter


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
    readonly_fields = ('vendor', 'profile_type','is_updated_in_crm','zoho_crm_id', 'is_draft', 'step', 'number_of_legal_entities',)
    form = VendorProfileForm
    inlines = [InlineVendorProfileContactAdmin,InlineProfileOverviewAdmin,InlineFinancialOverviewAdmin,InlineProcessingOverviewAdmin,InlineProgramOverviewAdmin,InlineLicenseAdmin,]
    


class MyVendorAdmin(nested_admin.NestedModelAdmin):#(admin.ModelAdmin):
    """
    Configuring Vendors
    """
    inlines = [InlineVendorProfileAdmin, InlineVendorUserAdmin,]
    extra = 0
    model = Vendor
    readonly_fields = ('ac_manager','vendor_category','created_on','updated_on')
    list_display = ('vendor_category','profile_name','ac_manager',)
    search_fields = ('ac_manager__email','vendor_category',)
    list_filter = (
        ('created_on', DateRangeFilter), ('updated_on', DateRangeFilter),
    )
    #list_per_page = 50
         
            
admin.site.register(Vendor,MyVendorAdmin)
