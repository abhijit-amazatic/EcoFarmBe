"""
Admin related customization.
"""

import json
from django.contrib import admin
from django.db import models
from django import forms
from core.mailer import mail, mail_send
from django.conf import settings
from django.contrib.postgres import fields
from django.contrib.admin import widgets
from django.db import transaction
from django_json_widget.widgets import JSONEditorWidget
import nested_admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from user.models import (User,)
from django.contrib import messages
from django.utils import timezone
from django_reverse_admin import ReverseModelAdmin
from multiselectfield import MultiSelectField

from integration.box import (delete_file,)
from integration.tasks import (insert_record_to_crm,)
from .tasks import (invite_profile_contacts,)
from core.utility import (send_async_approval_mail, get_profile_type,send_async_approval_mail_admin,)
from .models import (
    Organization,
    Brand,License,
    ProfileContact,
    LicenseProfile,
    CultivationOverview,
    NurseryOverview,
    ProgramOverview,
    FinancialOverview,
    CropOverview,
    ProfileCategory,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
)
from utils import (reverse_admin_change_path,)
from import_export.admin import (ImportExportModelAdmin, ExportActionMixin)
from import_export import resources

class LicenseResource(resources.ModelResource):
    
    class Meta:
        model = License
        fields = ('id','status','step','legal_business_name','license_profile__name','license_profile__county','license_profile__appellation','brand__brand_name','created_by__email','organization__name','client_id','license_type', 'owner_or_manager','business_dba', 'license_number','expiration_date', 'issue_date','premises_address','premises_county','business_structure','tax_identification', 'ein_or_ssn','premises_city','zip_code','premises_apn', 'premises_state','uploaded_license_to', 'uploaded_sellers_permit_to','uploaded_w9_to','associated_program', 'profile_category', 'is_buyer','is_seller','is_updated_in_crm','zoho_crm_id','zoho_books_customer_ids', 'zoho_books_vendor_ids', 'is_data_fetching_complete','status_before_expiry', 'is_notified_before_expiry', 'is_updated_via_trigger','is_contract_downloaded', 'crm_output','books_output', 'license_status','created_on','updated_on','license_profile__region','license_profile__ethics_and_certification','license_profile__product_of_interest','license_profile__cultivars_of_interest','license_profile__signed_program_name','license_profile__bank_account_number','license_profile__bank_routing_number','license_profile__bank_zip_code',)
        export_order = ('id','status','step','legal_business_name','license_profile__name','license_profile__county','license_profile__appellation','brand__brand_name','created_by__email','organization__name','client_id','license_type', 'owner_or_manager','business_dba', 'license_number','expiration_date', 'issue_date','premises_address','premises_county','business_structure','tax_identification', 'ein_or_ssn','premises_city','zip_code','premises_apn', 'premises_state','uploaded_license_to', 'uploaded_sellers_permit_to','uploaded_w9_to','associated_program', 'profile_category', 'is_buyer','is_seller','is_updated_in_crm','zoho_crm_id','zoho_books_customer_ids', 'zoho_books_vendor_ids', 'is_data_fetching_complete','status_before_expiry', 'is_notified_before_expiry', 'is_updated_via_trigger','is_contract_downloaded', 'crm_output','books_output', 'license_status','created_on','updated_on','license_profile__region','license_profile__ethics_and_certification','license_profile__product_of_interest','license_profile__cultivars_of_interest','license_profile__signed_program_name','license_profile__bank_account_number','license_profile__bank_routing_number','license_profile__bank_zip_code',)
        
class LicenseUpdatedForm(forms.ModelForm):

    class Meta:
        model = License
        fields = '__all__'

    def clean(self):        
        if self.changed_data:
            if 'status' in self.changed_data and self.cleaned_data.get('status') == 'approved':
                license_obj = License.objects.filter(id=self.instance.id)
                if license_obj:
                    ac_manager = license_obj[0].created_by.email
                    profile_type = get_profile_type(license_obj[0])
                    admin_link = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(license_obj[0])}"
                    mail_send("farm-approved.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login', 'profile_type': profile_type,'legal_business_name': license_obj[0].legal_business_name},"Your %s profile has been approved."% profile_type, ac_manager)
                    #admin mail send after approval
                    mail_send("farm-approved-admin.html",{'admin_link': admin_link,'mail':self.request.user.email,'license_type':license_obj[0].license_type,'legal_business_name':license_obj[0].legal_business_name,'license_number':license_obj[0].license_number},"License Profile [%s] approved" % license_obj[0].license_number, recipient_list=settings.ONBOARDING_ADMIN_EMAIL)
                    

def approve_license_profile(modeladmin, request, queryset):
    """
    Function for bulk profile approval.
    """
    for profile in queryset:
        if profile.status != 'approved':
            profile.status ='approved'
            profile.save()
            license_profile = LicenseProfile.objects.filter(license=profile)
            if license_profile:
                license_profile[0].approved_on  = timezone.now()
                license_profile[0].approved_by = get_user_data(request)
                license_profile[0].save()
            send_async_approval_mail.delay(profile.id)
            send_async_approval_mail_admin.delay(profile.id,request.user.id)
            if hasattr(profile, 'profile_contact'):
                invite_profile_contacts.delay(profile.profile_contact.id)
                pass#add_users_to_system_and_license.delay(profile.profile_contact.id,profile.id)
                
    messages.success(request,'License Profiles Approved!')    
approve_license_profile.short_description = 'Approve Selected License Profiles'



def get_obj_file_ids(obj):
    """
    Extract box file ids
    """
    box_file_ids = []
    #doc_field = ['uploaded_license_to','uploaded_sellers_permit_to']
    links = License.objects.filter(id=obj.id).values('uploaded_license_to','uploaded_sellers_permit_to')
    to_be_removed = [ v for k, v in links[0].items() if v is not None]
    try:
        if links:
            for doc in to_be_removed:
                if '?id=' in doc:
                    box_id = doc.split('?id=')[1]
                else:
                    box_id = doc
                if box_id:     
                    box_file_ids.append(box_id)
            return box_file_ids
    except Exception as e:
        print('exception',e)
        
            

def delete_model(modeladmin, request, queryset):
    for obj in queryset:
        file_ids = get_obj_file_ids(obj)
        if file_ids:
            for file_id in file_ids:
                print('FileID to delete from box:',file_id)
                delete_file(file_id)
        obj.delete()
delete_model.short_description = "Delete selected License Profile and it's box files"

def sync_records(modeladmin, request, queryset):
    for record in queryset:
        insert_record_to_crm.delay(
            license_id=record.id,
            is_update=False)
sync_records.short_description = "Insert Records To CRM"

def update_records(modeladmin, request, queryset):
    for record in queryset:
        insert_record_to_crm.delay(
            license_id=record.id,
            is_update=True)
update_records.short_description = "Update Records To CRM"

def update_status_to_in_progress(modeladmin, request, queryset):
    for profile in queryset:
        profile.status = 'in_progress'
        profile.save()
    messages.success(request,'Status Updated to in_progress!')    
update_status_to_in_progress.short_description = "Update Status To in_progress"

class ProfileContactForm(forms.ModelForm):
    class Meta:
        model = ProfileContact
        fields = '__all__'
        widgets = {
            'profile_contact_details': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
        
class InlineLicenseProfileContactAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    extra = 0
    model = ProfileContact
    readonly_fields = ('is_draft',)
    can_delete = False
    form = ProfileContactForm


class CultivationForm(forms.ModelForm):
    class Meta:
        model = CultivationOverview
        fields = '__all__'
        widgets = {
            'overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }
        

class InlineCultivationOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for CultivationOverview.
    """
    extra = 0
    model = CultivationOverview
    readonly_fields = ('is_draft','overview',)
    can_delete = False
    form = CultivationForm

class InlineNurseryOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for NurseryOverview.
    """
    extra = 0
    model = NurseryOverview
    can_delete = False
    #readonly_fields = ('is_draft','overview',)
    
class FinancialForm(forms.ModelForm):
    class Meta:
        model = FinancialOverview
        fields = '__all__'
        widgets = {
            'overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }


class InlineFinancialOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for FinancialOverview model.
    """
    extra = 0
    model = FinancialOverview
    can_delete = False
    readonly_fields = ('is_draft','overview',)
    form = FinancialForm


class CropForm(forms.ModelForm):
    class Meta:
        model = CropOverview
        fields = '__all__'
        widgets = {
            'overview': JSONEditorWidget(options={'modes':['code','text'],'search': True}),
        }        


class InlineCropOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for InlineCropOverview model.
    """
    extra = 0
    model = CropOverview
    can_delete = False
    readonly_fields = ('is_draft','overview',)
    form = CropForm


class InlineProgramOverviewAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for InlineProgramOverviewAdmin  model
    """
    extra = 0
    model = ProgramOverview
    can_delete = False
    readonly_fields = ('is_draft',)


class InlineLicenseProfileAdmin(nested_admin.NestedStackedInline):
    """
    Configuring field admin view for InlineLicenseProfile  model
    """
    extra = 0
    model = LicenseProfile
    can_delete = False
    readonly_fields = ('is_draft', 'agreement_signed')


# class InlineLicenseUserAdmin(nested_admin.NestedTabularInline):
#     extra = 0
#     model = LicenseUser


def get_user_data(request):
    """
    return user info dict.
    """
    return {'id':request.user.id,
            'email':request.user.email,
            'first_name':request.user.first_name,
            'last_name':request.user.last_name}
        

class MyLicenseAdmin(ImportExportModelAdmin,nested_admin.NestedModelAdmin):
    """
    #ExportActionMixin
    #ImportExportModelAdmin
    Configuring License
    """
    def approved_on(self, obj):
        return obj.license_profile.approved_on

    def name(self, obj):
        return obj.license_profile.name

    def approved_by(self, obj):
        if obj.license_profile.approved_by:
            return obj.license_profile.approved_by.get('email',"N/A")
        return "N/A"

    def zoho_crm_account_id(self, obj):
        if obj.license_profile:
            return obj.license_profile.zoho_crm_account_id

    def zoho_crm_vendor_id(self, obj):
        if obj.license_profile:
            return obj.license_profile.zoho_crm_vendor_id

    def get_search_results(self, request, queryset, search_term):
        """
        Default and custom search filter for farm names.
        """
        queryset, use_distinct = super(MyLicenseAdmin, self).get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.select_related('license_profile').filter(license_profile__name__contains={'name':search_term})
        return queryset, use_distinct
    
    name.admin_order_field = 'license_profile__name'
    inlines = [InlineLicenseProfileAdmin,InlineLicenseProfileContactAdmin,InlineCultivationOverviewAdmin,InlineNurseryOverviewAdmin,InlineFinancialOverviewAdmin,InlineCropOverviewAdmin,InlineProgramOverviewAdmin,]
    resource_class = LicenseResource
    form = LicenseUpdatedForm
    extra = 0
    model = License
    list_display = ('name', 'organization','license_number','legal_business_name', 'client_id', 'status','profile_category','brand', 'zoho_crm_id', 'zoho_crm_account_id', 'zoho_crm_vendor_id', 'approved_on','approved_by','created_on','updated_on',)
    list_select_related = ['brand__organization__created_by', 'organization__created_by']
    search_fields = ('brand__brand_name', 'brand__organization__created_by__email', 'organization__name', 'organization__created_by__email', 'status','license_number', 'legal_business_name')
    readonly_fields = ('created_on','updated_on', 'client_id', 'crm_output', 'books_output')
    list_filter = (
        ('created_on', DateRangeFilter), ('updated_on', DateRangeFilter),'status','profile_category','is_contract_downloaded','license_type',
    )
    ordering = ('-created_on','legal_business_name','status','updated_on',)
    actions = [approve_license_profile, update_status_to_in_progress, delete_model, sync_records, update_records]
    list_per_page = 50

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'approved':
            send_async_approval_mail.delay(obj.id)
            send_async_approval_mail_admin.delay(obj.id,request.user.id)
            license_profile = LicenseProfile.objects.filter(license=obj)
            if license_profile:
                license_profile[0].approved_on  = timezone.now()
                license_profile[0].approved_by = get_user_data(request)
                license_profile[0].save()
            if hasattr(obj, 'profile_contact'):
                invite_profile_contacts.delay(obj.profile_contact.id)
                pass #add_users_to_system_and_license.delay(obj.profile_contact.id,obj.id)
            
        super().save_model(request, obj, form, change)

    def get_form(self, request, *args, **kwargs):
        form = super(MyLicenseAdmin, self).get_form(request, *args, **kwargs)
        form.request = request
        return form    

class OrganizationRoleNestedAdmin(nested_admin.NestedTabularInline):
    """
    OrganizationRoleAdmin
    """
    extra = 0
    model = OrganizationRole
    readonly_fields = ('created_on','updated_on',)
    formfield_overrides = {
        # models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
        models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
    }


class OrganizationUserRoleNestedAdmin(nested_admin.NestedTabularInline):
    extra = 0
    model = OrganizationUserRole
    readonly_fields = ('created_on','updated_on',)
    formfield_overrides = {
        models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
    }

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'role':
            if request._organization is not None:
                field.queryset = field.queryset.filter(organization=request._organization)
            else:
                field.queryset = field.queryset.none()
        return field

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == 'licenses':
            if request._organization is not None:
                field.queryset = field.queryset.filter(organization=request._organization)
            else:
                field.queryset = field.queryset.none()
        return field

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
        return formfield


class OrganizationUserNestedAdmin(nested_admin.NestedTabularInline):
    extra = 0
    model = OrganizationUser
    readonly_fields = ('created_on','updated_on',)
    inlines = [OrganizationUserRoleNestedAdmin]


class OrganizationResource(resources.ModelResource):

    class Meta:
        model = Organization
        fields = (
            'id',
            'name', 
            'created_by__email', 
            'zoho_crm_id', 
            'is_updated_in_crm',
            'email', 
            'phone', 
            'category', 
            'about', 
            'ethics_and_certifications',
            'created_on',
            'updated_on',
        )

        
class OrganizationAdmin(ExportActionMixin,nested_admin.NestedModelAdmin):
    """
    Configuring brand
    """
    model = Organization
    list_display = ('name', 'created_by', 'created_on', 'updated_on',)
    search_fields = ('name', 'created_by__email',)
    list_filter = (
        ('created_on', DateRangeFilter),
        ('updated_on', DateRangeFilter),
    )
    ordering = ('-created_on', 'updated_on',)
    inlines = [OrganizationRoleNestedAdmin, OrganizationUserNestedAdmin]
    resource_class = OrganizationResource

    def get_form(self, request, obj=None, **kwargs):
        request._organization = obj
        return super().get_form(request, obj, **kwargs)


class MyBrandAdmin(admin.ModelAdmin):
    """
    Configuring brand
    """    
    extra = 0
    model = Brand
    #inlines = [InlineAccountLicenseAdmin,InlineAccountBasicProfileAdmin,InlineAccountContactInfoAdmin, InlineAccountUserAdmin]
    list_display = ('brand_name','organization', 'appellation','created_on', 'updated_on',)
    search_fields = ('brand_name', 'organization', 'appellation')
    list_filter = (
        ('created_on', DateRangeFilter),('updated_on',DateRangeFilter ),
    )
    ordering = ('-created_on','updated_on',)

    
class ProfileCategoryAdmin(admin.ModelAdmin):
    """
    ProfileCategoryAdmin
    """
    #search_fields = ('',)


# class OrganizationRoleAdmin(admin.ModelAdmin):
#     """
#     OrganizationRoleAdmin
#     """
#     readonly_fields = ('created_on','updated_on',)

#     formfield_overrides = {
#         # models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
#         models.ManyToManyField: {'widget': widgets.FilteredSelectMultiple("Permission", is_stacked=False)},
#     }


admin.site.register(Organization, OrganizationAdmin)
# admin.site.register(OrganizationRole,OrganizationRoleAdmin)
admin.site.register(Brand,MyBrandAdmin)
admin.site.register(License,MyLicenseAdmin)
admin.site.register(ProfileCategory, ProfileCategoryAdmin)

