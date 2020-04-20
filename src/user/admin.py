"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from core.mailer import mail
from django.conf import settings
from .models import (User, MemberCategory,)


# class UserForm(forms.ModelForm):
#     manual_activation = forms.BooleanField()  # a flag which determines if the user should be manually activated

#     class Meta:
#         model = User
#         fields = '__all__'


#     def clean(self):
#         manual_activation = self.cleaned_data.pop('manual_activation', False)  
#         if manual_activation:
#              # send_email logics
#             #mail("verification-send.html",{'link': link},"Eco-Farm Verification.", instance.email)
#             print("self.cleaned_data.pop('manual_activation', False)", self.cleaned_data.pop('manual_activation', False)  )
#             print("self.instance\n", self.instance)

#         return self.cleaned_data

class UserAdmin(admin.ModelAdmin):
    """
    Configuring User
    """
    #form = UserForm
    list_per_page = 50
    readonly_fields = ['zoho_contact_id']
    search_fields = ('username', 'legal_business_name', 'email',)

    def save_model(self, request, obj, form, change):
        if obj.is_approved:
            mail("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME},"Account Approved.", obj.email)
        super().save_model(request, obj, form, change)

class MemberCategoryAdmin(admin.ModelAdmin):
    """
    MemberAdmin
    """
    #search_fields = ('',)
    

admin.site.register(User, UserAdmin)
admin.site.register(MemberCategory, MemberCategoryAdmin)  



