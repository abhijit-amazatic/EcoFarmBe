"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from core.mailer import mail, mail_send
from django.conf import settings
from datetime import datetime
from .models import (User, MemberCategory,)
from vendor.models import (Vendor,VendorProfile,)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.db import transaction
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
        

class InlineVendorProfileAdmin(nested_admin.NestedTabularInline):#(admin.TabularInline):#
    """
    Configuring field admin view for VendorProfile model
    """
    extra = 0
    model = VendorProfile
    fk_name = 'vendor'
    readonly_fields = ('vendor', 'profile_type','number_of_licenses','is_updated_in_crm','number_of_legal_entities','zoho_crm_id', 'is_draft', 'step',)
    #form = VendorProfileForm

        
        
class VendorInlineAdmin(nested_admin.NestedTabularInline):#(admin.StackedInline):
    """
    Configuring field admin view for vendor model
    """
    extra = 0
    model = Vendor
    verbose_name_plural = ('Vendors')
    can_delete = False
    inlines = [InlineVendorProfileAdmin]
    
    #list_display = ('ac_manager', 'vendor_category', )
    #readonly_fields = ['vendor_category']
    
    
      
        
class MyUserAdmin(nested_admin.NestedModelAdmin,):#(UserAdmin):

    #inlines = [VendorInlineAdmin]
    form = MyUserChangeForm
    list_display = ('email', 'is_approved', )
    list_filter = ('is_approved', 'is_verified')
    list_per_page = 25
    search_fields = ('username', 'legal_business_name', 'email',)
    readonly_fields = ['is_verified']
    fieldsets = UserAdmin.fieldsets + (
            (('User'), {'fields': ('is_approved','is_verified',)}),
    )     
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if 'is_approved' in form.changed_data and obj.is_approved:
            mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login'},"Account Approved.", obj.email)
        super().save_model(request, obj, form, change)

        

class MemberCategoryAdmin(admin.ModelAdmin):
    """
    MemberAdmin
    """
    #search_fields = ('',)

#admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
admin.site.register(MemberCategory, MemberCategoryAdmin)  
    
        
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




