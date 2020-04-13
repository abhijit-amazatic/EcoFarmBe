"""
Admin related customization.
"""
from django.contrib import admin
from .models import (Vendor, VendorCategory,)



class VendorCategoryAdmin(admin.ModelAdmin):
    """
    VendorCategory Admin
    """
    #search_fields = ('',)
    

admin.site.register(VendorCategory, VendorCategoryAdmin)      
