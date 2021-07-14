"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from core.mailer import mail, mail_send
from django.conf import settings
from django.db import models
from datetime import datetime
from .models import (User, MemberCategory,TermsAndCondition, TermsAndConditionAcceptance, HelpDocumentation)
from .views import (create_contact_license_linking, )
from core.utility import (send_async_user_approval_mail, send_verification_link_user_instance,)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.db import transaction
from django.contrib import messages
from django.shortcuts import reverse
from django.utils import timezone
import nested_admin
from ckeditor.fields import RichTextField       
from core.widgets import CKEditorWidget
from django.http import HttpResponseRedirect
from integration.crm import (create_records, update_records, )

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

def sync_records(modeladmin, request, queryset):
    result = list()
    for record in queryset:
        r = dict()
        record.__dict__['phone'] = record.__dict__['phone'].as_international
        create_response = create_records('Contacts', record.__dict__)
        r['Contact'] = create_response
        if create_response['status_code'] in [201, 202]:
            if record.legal_business_name:
                response = create_contact_license_linking(record, create_response)
                r['License_X_Contact'] = response
        result.append(r)
    messages.success(request, result)
sync_records.short_description = "Insert Records To CRM"

class MyUserAdmin(UserAdmin,):#nested_admin.NestedModelAdmin,
    
    def approved_by_member(self, obj):
        if hasattr(obj,'approved_by') and obj.approved_by is not None :
           return obj.approved_by.get('email',"N/A")
        else:
            return "N/A"
        

    # def created_on(self,obj):
    #     return obj.created_on
    
    #inlines = [VendorInlineAdmin]
    form = MyUserChangeForm
    change_form_template = 'user/custom_user_change_form.html'
    list_display = ('email', 'is_approved', 'phone', 'approved_on','last_login','approved_by_member','date_joined',)
    list_filter = ('is_approved', 'is_verified',)
    list_per_page = 25
    search_fields = ('username','email',)
    ordering = ('-date_joined',)
    readonly_fields = ['is_verified','approved_on','is_2fa_enabled','approved_by','created_on','updated_on','is_phone_verified','unique_user_id',] #'phone'
    actions = [approve_user, sync_records, ]
    filter_horizontal = ('groups', 'user_permissions', 'internal_roles')
    fieldsets = UserAdmin.fieldsets + (
            (('User'), {'fields': ('full_name','phone', 'country','state','date_of_birth','city','zip_code','recovery_email','alternate_email','is_phone_verified','legal_business_name','business_dba','existing_member','membership_type','is_updated_in_crm','profile_photo','profile_photo_sharable_link','website','title','department','instagram','facebook','twitter','linkedin','about','zoho_crm_id','is_approved','approved_on','approved_by','is_verified','crm_link','bypass_terms_and_conditions','unique_user_id', 'default_org')}),
            (('Internal Permission'), {'fields': ('internal_roles',)}),
    )

    def response_change(self, request, obj):
        if "_resend-mail" in request.POST:
            send_verification_link_user_instance(obj)
            self.message_user(request, "Verification Link sent!")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        # if change and 'email' in form.changed_data:
        #     if not form.initial['email'].lower() == obj.email.lower():
        #         obj.is_verified = False
        #         send_verification_link_user_instance(obj)

        if 'is_approved' in form.changed_data and obj.is_approved:
            mail_send("approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login','full_name': obj.full_name},"Account Approved.", obj.email)
            obj.approved_on  = timezone.now()
            obj.approved_by = get_user_data(request)
            obj.save()
        super().save_model(request, obj, form, change)





class MemberCategoryAdmin(admin.ModelAdmin):
    """
    MemberAdmin
    """
    #search_fields = ('',)


class TermsAndConditionForm(forms.ModelForm):
    terms_and_condition = forms.CharField(widget=CKEditorWidget())
    class Meta:
        model = TermsAndCondition
        fields = '__all__'
        widgets = {
            'terms_and_condition': CKEditorWidget(),
        }


class TermsAndConditionAdmin(admin.ModelAdmin):
    """
    TermsAndConditionAdmin
    """
    form = TermsAndConditionForm
    list_display = ('profile_type', 'publish_from', 'created_on',)
    list_filter = ('profile_type',)
    list_per_page = 25
    ordering = ('-created_on', '-publish_from',)
    readonly_fields = ('created_on','updated_on',)
    fields = ('profile_type', 'terms_and_condition', 'publish_from', 'created_on', 'updated_on')

    # def get_readonly_fields(self, request, obj=None):
    #     fields = super().get_readonly_fields(request, obj=obj)
    #     if obj and obj.publish_from <= timezone.now().date():
    #         fields = ('profile_type', 'terms_and_condition', 'publish_from') + fields
    #     return fields

    def has_change_permission(self, request, obj=None):
        if obj and obj.publish_from <= timezone.now().date():
            return False
        return super(TermsAndConditionAdmin, self).has_change_permission(request, obj)

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     if obj and obj.publish_from <= timezone.now().date():
    #         form.base_fields['terms_and_condition'] = forms.CharField(widget=CKEditorWidget())
    #         form.base_fields['terms_and_condition'].widget = CKEditorWidget()
    #         form.base_fields['terms_and_condition'].widget.attrs["disabled"] = "disabled"
    #         form.base_fields['terms_and_condition'].disabled = True
    #     return form


    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        admin_form = context['adminform']
        form = admin_form.form
        if 'terms_and_condition' in admin_form.readonly_fields:
            form.fields['terms_and_condition'] = forms.CharField(widget=CKEditorWidget())
            form.fields['terms_and_condition'].widget = CKEditorWidget()
            form.fields['terms_and_condition'].disabled = True
            form.initial['terms_and_condition'] = form.instance.terms_and_condition
            admin_form.readonly_fields = tuple(x for x in context['adminform'].readonly_fields if x !='terms_and_condition')
        return super().render_change_form(request, context, add=add, change=change, obj=obj, form_url=form_url)


class TermsAndConditionAcceptanceAdmin(admin.ModelAdmin):
    """
    TermsAndConditionAcceptanceAdmin
    """
    list_display = ('user', 'is_accepted', 'terms_and_condition', 'ip_address', 'created_on',)
    list_filter = ('is_accepted',)
    list_per_page = 25
    search_fields = ('user__email',)
    ordering = ('-created_on',)
    readonly_fields = ('terms_and_condition_id', 'ip_address', 'user_agent', 'hostname', 'created_on','updated_on',)
    fields = ('user', 'terms_and_condition_id', 'terms_and_condition', 'is_accepted', 'ip_address', 'user_agent', 'hostname', 'created_on','updated_on',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if isinstance(obj, TermsAndConditionAcceptance):
            if request.path.startswith(reverse("admin:user_termsandconditionacceptance_changelist")):
                return False
        return True

class HelpDocumentationAdmin(admin.ModelAdmin):
    """
    HelpDocumentationAdmin
    """
    list_display = ('title', 'url','ordering','for_page','created_on',)
    list_filter = ('title',)
    list_per_page = 25
    ordering = ('-created_on',)
    readonly_fields = ('created_on','updated_on',)
    fields = ('title', 'url', 'ordering','for_page', 'content','created_on', 'updated_on')

    
#admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
admin.site.register(MemberCategory, MemberCategoryAdmin)
admin.site.register(TermsAndCondition, TermsAndConditionAdmin)
admin.site.register(TermsAndConditionAcceptance, TermsAndConditionAcceptanceAdmin)
admin.site.register(HelpDocumentation, HelpDocumentationAdmin)

# admin.site.site_header = "Thrive Society - Eco Farm Administration"
# admin.site.site_title = "Thrive Society - Eco Farm App Administration"
# admin.site.index_title = "Welcome to Thrive Society - Eco Farm App"
        
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




