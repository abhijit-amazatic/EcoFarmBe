"""
Admin related customization.
"""
from django.contrib import admin
from django import forms
from core.mailer import mail, mail_send
from django.conf import settings
from .models import (Vendor,VendorProfile,VendorUser,ProfileContact, ProfileOverview, FinancialOverview, ProcessingOverview, ProgramOverview, License)
from user.models import (User, MemberCategory,)
import nested_admin



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

    

class InlineVendorProfileContactAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProfileContact model
    """
    extra = 0
    model = ProfileContact
    fields = ('profile_contact_details',)
    readonly_fields = ('profile_contact_details',)
    list_display = ('profile_contact_details',)
    can_delete = False
    
    

class InlineProfileOverviewAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProfileOverview model
    """
    extra = 0
    model = ProfileOverview
    fields = ('profile_overview',)
    readonly_fields = ('profile_overview',)
    can_delete = False

class InlineFinancialOverviewAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for FinancialOverview model
    """
    extra = 0
    model = FinancialOverview
    fields = ('financial_details',)
    readonly_fields = ('financial_details',)
    can_delete = False

class InlineProcessingOverviewAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProcessingOverview model
    """
    extra = 0
    model = ProcessingOverview
    fields = ('processing_config',)
    readonly_fields = ('processing_config',)
    can_delete = False
    
class InlineProgramOverviewAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):
    """
    Configuring field admin view for ProgramOverview model
    """
    extra = 0
    model = ProgramOverview
    fields = ('program_details',)
    readonly_fields = ('program_details',)
    can_delete = False

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
    readonly_fields = ('ac_manager','vendor_category',)
    list_display = ('vendor_category','ac_manager',)
    search_fields = ('ac_manager__email','vendor_category',)
    #list_per_page = 50
    #search_fields = ('ac_manager__email',)



admin.site.register(Vendor,MyVendorAdmin)
