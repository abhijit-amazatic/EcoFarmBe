"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from core.mailer import mail, mail_send
from django.conf import settings
from datetime import datetime
from .models import (User, MemberCategory,)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm



class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

        
class MyUserAdmin(UserAdmin):
    form = MyUserChangeForm
    list_display = ('email', 'is_approved', )
    list_filter = ('is_approved', 'is_verified')
    list_per_page = 25
    search_fields = ('username', 'legal_business_name', 'email',)
    fieldsets = UserAdmin.fieldsets + (
            (None, {'fields': ('is_approved',)}),
    )


    def save_model(self, request, obj, form, change):
        if obj.is_approved:
            mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME},"Account Approved.", obj.email)
        super().save_model(request, obj, form, change)

    
        
# class UserForm(forms.ModelForm):
#     manual_activation = forms.BooleanField()  # a flag which determines if the user should be manually activated

#     class Meta:
#         model = User
#         fields = '__all__'


#     def clean(self):
#         manual_activation = self.cleaned_data.pop('manual_activation', False)  
#         if manual_activation:
#              # send_email logics
#             #mail_send("verification-send.html",{'link': link},"Eco-Farm Verification.", instance.email)
#             print("self.cleaned_data.pop('manual_activation', False)", self.cleaned_data.pop('manual_activation', False)  )
#             print("self.instance\n", self.instance)

#         return self.cleaned_data

# class UserAdmin(admin.ModelAdmin):
#     """
#     Configuring User
#     """
#     #form = UserForm
#     list_per_page = 50
#     readonly_fields = ['zoho_contact_id']
#     search_fields = ('username', 'legal_business_name', 'email',)
#     list_display = ('email', 'is_approved','is_verified', )
#     list_filter = ('is_approved', 'is_verified')


#     def save_model(self, request, obj, form, change):
#         if obj.is_approved:
#             mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME},"Account Approved.", obj.email)
#         super().save_model(request, obj, form, change)

class MemberCategoryAdmin(admin.ModelAdmin):
    """
    MemberAdmin
    """
    #search_fields = ('',)
    
admin.site.register(User, MyUserAdmin)
admin.site.register(MemberCategory, MemberCategoryAdmin)  



