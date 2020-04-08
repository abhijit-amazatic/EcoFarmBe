"""
Admin related customization.
"""
from django.contrib import admin
from .models import (Vendor, CultivatorCategory,)



class CultivatorCategoryAdmin(admin.ModelAdmin):
    """
    CultivatorCategory Admin
    """
    #search_fields = ('',)
    

admin.site.register(CultivatorCategory, CultivatorCategoryAdmin)      
