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
from .models import (Account,AccountLicense, AccountBasicProfile, AccountContactInfo, )


class MyAccountAdmin(admin.ModelAdmin):#(nested_admin.NestedModelAdmin):
    """
    Configuring Account
    """
  
    extra = 0
    model = Account
    #list_display = ()
    #list_select_related = []
    #search_fields = ()
    #readonly_fields = ()
    #ordering = ('status','approved_on','created_on','updated_on')
    list_per_page = 50


#admin.site.register(Account,MyAccountAdmin)

