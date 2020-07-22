"""
Admin related customization.
"""
import json
from django.contrib import admin
from django import forms
from core.mailer import mail, mail_send
from django.conf import settings
from django.contrib.postgres import fields
from django.db import transaction
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from user.models import (User,)
from django.contrib import messages
from django.utils import timezone
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from .models import (Account,AccountLicense, AccountBasicProfile, AccountContactInfo,AccountUser,AccountCategory)
from core.utility import (send_async_account_approval_mail,)
from integration.crm import (insert_accounts, )


class InlineAccountLicenseAdmin(admin.StackedInline):
    """
    Configuring field admin.
    """
    extra = 0
    model = AccountLicense
    readonly_fields = ('license_number',)
    can_delete = False

class InlineAccountUserAdmin(admin.TabularInline):
    """
    Configuring field admin.
    """
    extra = 0
    model = AccountUser
    #readonly_fields = ('license_number',)
    #can_delete = False        

class InlineAccountBasicProfileAdmin(admin.StackedInline):
    """
    Configuring field admin AccountBasicProfile
    """
    extra = 0
    model = AccountBasicProfile

class InlineAccountContactInfoAdmin(admin.StackedInline):
    """
    Configuring field admin.
    """
    extra = 0
    model = AccountContactInfo
    
def approve_accounts(modeladmin, request, queryset):
    """
    Function for bulk accounts approval.
    """
    for account in queryset:
        if account.status == 'approved':
            pass #can add custom logic here in future.
        else:
            account.status ='approved'
            account.approved_on  = timezone.now()
            account.approved_by = get_user_data(request)
            account.save()
            send_async_account_approval_mail.delay(account.id)
            insert_accounts.delay(account_id=account.id)
                
    messages.success(request,'Accounts Approved!')    
approve_accounts.short_description = 'Approve Selected Accounts'

def get_user_data(request):
    """
    return user info dict.
    """
    return {'id':request.user.id,
            'email':request.user.email,
            'first_name':request.user.first_name,
            'last_name':request.user.last_name}


class MyAccountAdmin(admin.ModelAdmin):#(nested_admin.NestedModelAdmin):
    """
    Configuring Account
    """

    def company_name(self, obj):
        return obj.account_profile.company_name

    def website(self, obj):
        return obj.account_contact.website

    def approved_by_member(self, obj):
        return obj.approved_by.get('email',"N/A")
    
    extra = 0
    model = Account
    inlines = [InlineAccountLicenseAdmin,InlineAccountBasicProfileAdmin,InlineAccountContactInfoAdmin, InlineAccountUserAdmin]
    list_display = ('company_name','status','website','account_category', 'created_on', 'approved_on', 'approved_by_member',)
    search_fields = ('account_profile__company_name','account_contact__website','account_category','status',)
    list_filter = (
        ('created_on', DateRangeFilter),('approved_on',DateRangeFilter ),'status',
    )
    ordering = ('-created_on','status','approved_on',)
    actions = [approve_accounts, ] 

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'approved':
            send_async_account_approval_mail(obj.id)
            insert_accounts.delay(account_id=obj.id)
            obj.approved_on  = timezone.now()
            obj.approved_by = get_user_data(request)
            obj.save()
        super().save_model(request, obj, form, change)

    
    
class AccountCategoryAdmin(admin.ModelAdmin):
    """
    AccountAdmin.
    """
    #search_fields = ('',)

admin.site.register(Account,MyAccountAdmin)
admin.site.register(AccountCategory, AccountCategoryAdmin)  
