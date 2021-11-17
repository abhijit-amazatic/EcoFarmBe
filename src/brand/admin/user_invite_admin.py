"""
Admin related customization.
"""

from django import forms
from django.utils import timezone
from django.contrib import admin
from django.db import models
from django.shortcuts import (
    reverse,
)

from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from core.mixins.admin import CustomButtonMixin
from ..tasks import (
    send_async_invitation,
)
from ..models import LicenseUserInvite


# class OrganizationUserInviteAdmin(admin.ModelAdmin):
#     """
#     OrganizationUserInviteAdmin
#     """
#     filter_horizontal = ['licenses', ]


class LicenseUserInviteAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    LicenseUserInviteAdmin
    """

    filter_horizontal = [
        "roles",
    ]

    custom_buttons = ("resend_invite",)
    custom_buttons_prop = {
        "resend_invite": {
            "label": "Resend Invite",
            "color": "#f2910a",
        }
    }
    search_fields = (
        "email",
        "full_name",
        "phone",
        "assigned_roles",
        "license__license_number",
        "license__legal_business_name",
        "license__client_id",
        "license__organization",
    )

    list_display = (
        "email",
        "full_name",
        "phone",
        "assigned_roles",
        "license",
        "organization",
        "status",
        "is_invite_accepted",
        "created_by",
        "created_on",
        "updated_on",
    )

    list_filter = (
        "email",
        "status",
        "license",
        "license__organization",
        ("created_on", DateRangeFilter),
        ("updated_on", DateRangeFilter),
    )

    # search_fields = ('name',)
    # ordering = ('-name',)
    # readonly_fields = ('name',)
    actions = ("action_resend_invites",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('roles')
        qs = qs.select_related('license', 'license__organization', 'created_by')
        return qs

    def assigned_roles(self, obj):
        return ", ".join([x.name for x in obj.roles.all()])

    def organization(self, obj):
        return obj.license.organization

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def show_resend_invite_button(self, request, obj, add=False, change=False):
        if obj and change:
            if obj.status in ("pending", "user_joining_platform"):
                return True
        return False

    def resend_invite(self, request, obj):
        send_async_invitation.delay(obj.id)

    def action_resend_invites(self, request, queryset):
        for obj in queryset.filter(status__in=("pending", "user_joining_platform")):
            send_async_invitation.delay(obj.id)

    action_resend_invites.short_description = "Resend Selected Invites"
