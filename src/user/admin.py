"""
Admin related customization.
"""
from django.contrib import admin
from .models import (User, MemberCategory,)



class UserAdmin(admin.ModelAdmin):
    """
    Configuring User
    """
    list_per_page = 50
    readonly_fields = ['zoho_contact_id']
    search_fields = ('name', 'legal_business_name', 'email',)

class MemberCategoryAdmin(admin.ModelAdmin):
    """
    MemberAdmin
    """
    #search_fields = ('',)
    

admin.site.register(User, UserAdmin)
admin.site.register(MemberCategory, MemberCategoryAdmin)  
