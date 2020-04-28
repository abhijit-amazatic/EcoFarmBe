"""
Admin related customization.
"""
# from django.contrib import admin
# from .models import (Vendor,VendorProfile,)


# class InlineVendorProfileAdmin(admin.TabularInline):
#     """
#     Configuring field admin view for VendorProfile model
#     """
#     extra = 0
#     model = VendorProfile
#     readonly_fields = ['vendor', 'profile_type','is_updated_in_crm','zoho_crm_id', 'is_draft', 'step']

    
# class MyVendorAdmin(admin.ModelAdmin):
#     """
#     Configuring Vendors
#     """
#     inlines = (InlineVendorProfileAdmin, )
#     extra = 0
#     model = Vendor
#     readonly_fields = ['ac_manager','vendor_category']
#     list_display = ('vendor_category','ac_manager')
#     #list_per_page = 50
#     #search_fields = ('ac_manager__email',)



# admin.site.register(Vendor,MyVendorAdmin)
