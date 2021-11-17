"""
Admin related customization.
"""
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
import integration
from user.models import (User,)
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_reverse_admin import ReverseModelAdmin
from multiselectfield import MultiSelectField

from integration.box import (delete_file,)
from integration.tasks import (insert_record_to_crm, create_customer_in_books_task)
from ..tasks import (invite_profile_contacts,)
from ..models import (
    LicenseUserInvite
)


# class OrganizationUserInviteAdmin(admin.ModelAdmin):
#     """
#     OrganizationUserInviteAdmin
#     """
#     filter_horizontal = ['licenses', ]

class LicenseUserInviteAdmin(admin.ModelAdmin):
    """
    LicenseUserInviteAdmin
    """
    filter_horizontal = ['roles', ]


