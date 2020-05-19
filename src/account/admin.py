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
from .models import (Account,AccountLicense, AccountBasicProfile, AccountContactInfo, )


class InlineAccountLicenseAdmin(admin.StackedInline):
    """
    Configuring field admin.
    """
    extra = 0
    model = AccountLicense
    readonly_fields = ('license_number',)
    can_delete = False    

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
    inlines = [InlineAccountLicenseAdmin,InlineAccountBasicProfileAdmin,InlineAccountContactInfoAdmin]
    list_display = ('company_name','status','website','account_category', 'created_on', 'approved_on', 'approved_by_member',)
    search_fields = ('account_profile__company_name','account_contact__website','account_category','status',)
    list_filter = (
        ('created_on', DateRangeFilter),('approved_on',DateRangeFilter ),'status',
    )
    ordering = ('status','approved_on','created_on',)

    
    


admin.site.register(Account,MyAccountAdmin)

