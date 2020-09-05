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
from django_json_widget.widgets import JSONEditorWidget
import nested_admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from user.models import (User,)
from django.contrib import messages
from django.utils import timezone
from django_reverse_admin import ReverseModelAdmin
from .models import (Brand,ProfileCategory, )
#from core.utility import (send_async_approval_mail,get_encrypted_data,notify_employee_admin_to_verify_and_reset,)
#from integration.crm import (insert_vendors, )



class ProfileCategoryAdmin(admin.ModelAdmin):
    """
    ProfileCategoryAdmin
    """
    #search_fields = ('',)
    
admin.site.register(ProfileCategory, ProfileCategoryAdmin)  
