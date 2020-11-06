"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from core.mailer import mail, mail_send
from django.conf import settings
from datetime import datetime
from .models import (User, MemberCategory, TermsAndConditionAcceptance)
from core.utility import send_async_user_approval_mail
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
import nested_admin
       

class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    username = forms.CharField(required=False)

    # def clean(self):
    #     if self.cleaned_data.get('is_approved'):
    #         self.cleaned_data.pop('is_approved', False)
    #         return self.cleaned_data

        
    # def save(self, commit=True):
    #     user = super(MyUserChangeForm, self).save(commit=False)
    #     username = self.cleaned_data["username"]
    #     if username:
    #         print('in if username', username, type(username))
    #         user.username = username
    #     if commit:
    #         user.save()
    #     print("======USER", user)    
    #     return user
 
    #def clean(self):
        # if self.cleaned_data.get('is_approved'):
        #     mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME},"Account Approved.", self.cleaned_data.get('email'))
        #     return self.cleaned_data
            
def get_user_data(request):
    """
    return user info dict.
    """
    return {'id':request.user.id,
            'email':request.user.email,
            'first_name':request.user.first_name,
            'last_name':request.user.last_name}

def approve_user(modeladmin, request, queryset):
    """
    Function for bulk user approval.
    """
    for user in queryset:
        if not user.is_approved:
            user.is_approved = True
            user.approved_on = timezone.now()
            user.approved_by = get_user_data(request)
            user.save()
            send_async_user_approval_mail.delay(user.id)
                
    messages.success(request,'Users Approved!')    
approve_user.short_description = 'Approve Selected Users'      

class MyUserAdmin(nested_admin.NestedModelAdmin,):#(UserAdmin):
    
    def approved_by_member(self, obj):
        if hasattr(obj,'approved_by') and obj.approved_by is not None :
           return obj.approved_by.get('email',"N/A")
        else:
            return "N/A"
        

    # def created_on(self,obj):
    #     return obj.created_on
    
    #inlines = [VendorInlineAdmin]
    form = MyUserChangeForm
    list_display = ('email', 'is_approved', 'phone', 'approved_on','approved_by_member','date_joined',)
    list_filter = ('is_approved', 'is_verified',)
    list_per_page = 25
    search_fields = ('username','email',)
    ordering = ('-date_joined',)
    readonly_fields = ['is_verified','approved_on','approved_by','is_phone_verified','email'] #'phone'
    actions = [approve_user, ] 
    fieldsets = UserAdmin.fieldsets + (
            (('User'), {'fields': ('phone', 'is_phone_verified', 'is_approved','approved_on','approved_by','is_verified',)}),
    )     
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if 'is_approved' in form.changed_data and obj.is_approved:
            mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Account Approved.", obj.email)
            obj.approved_on  = timezone.now()
            obj.approved_by = get_user_data(request)
            obj.save()
        super().save_model(request, obj, form, change)





class MemberCategoryAdmin(admin.ModelAdmin):
    """
    MemberAdmin
    """
    #search_fields = ('',)


class TermsAndConditionAcceptanceAdmin(admin.ModelAdmin):
    """
    TermsAndConditionAcceptanceAdmin
    """
    # list_display = ('created_on','updated_on',)
    readonly_fields = ('ip_address', 'user_agent', 'hostname', 'created_on','updated_on',)
    
#admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
admin.site.register(MemberCategory, MemberCategoryAdmin)
admin.site.register(TermsAndConditionAcceptance, TermsAndConditionAcceptanceAdmin)
    
        
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




