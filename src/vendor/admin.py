"""
Admin related customization.
"""
from django.contrib import admin
from .models import (Vendor,VendorProfile,VendorUser,)


class VendorUserInline(admin.TabularInline):
    extra = 0
    model = VendorUser
    fields = ('user', 'role', )
    raw_id_fields = ('user', )
    autocomplete_lookup_fields = {
        'fk': ['user', ],
    }
    
class InlineVendorProfileAdmin(admin.TabularInline):
    """
    Configuring field admin view for VendorProfile model
    """
    extra = 0
    model = VendorProfile
    readonly_fields = ['vendor', 'profile_type','is_updated_in_crm','zoho_crm_id', 'is_draft', 'step', 'status']

    
class MyVendorAdmin(admin.ModelAdmin):
    """
    Configuring Vendors
    """
    inlines = (InlineVendorProfileAdmin, VendorUserInline)
    extra = 0
    model = Vendor
    readonly_fields = ['ac_manager','vendor_category']
    list_display = ('vendor_category','ac_manager')
    search_fields = ('ac_manager__email','vendor_category')
    #list_per_page = 50
    #search_fields = ('ac_manager__email',)



admin.site.register(Vendor,MyVendorAdmin)
