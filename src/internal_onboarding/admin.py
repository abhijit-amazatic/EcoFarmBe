from django.contrib import admin
from django.db import models
from django.shortcuts import (reverse, )


from core.mixins.admin import CustomButtonMixin
from django import forms
from .models import (
    InternalOnboardingInvite,
)
from .tasks import (
    send_internal_onboarding_invitation,
)


class InternalOnboardingInviteAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    Admin
    """
    verbose_name = "Invites"
    custom_buttons = ('resend_invite', )
    custom_buttons_prop = {
        'resend_invite': {
            'label': 'Resend Invite',
            'color': '#f2910a',
        }
    }

    list_display = (
        'user',
        'license',
        'assigned_roles',
        'organization',
        'status',
        'is_user_created',
        'created_by',
        'created_on',
        'updated_on',
    )
    # search_fields = ('name',)
    # ordering = ('-name',)
    # readonly_fields = ('name',)
    actions = ('resend_selected_invites', )

    def assigned_roles(self, obj):
        return ', '.join([x.name for x in obj.roles.all()])

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def show_resend_invite_button(self, request, obj, add=False, change=False):
        if obj and change:
            if obj.status in ('pending', 'accepted'):
                return True
        return False

    def resend_invite(self, request, obj):
        send_internal_onboarding_invitation.delay([obj.id])

    def resend_selected_invites(self, request, queryset):
        qs = queryset.filter(status__in=('pending', 'accepted'))
        send_internal_onboarding_invitation.delay(list(qs.values_list('id', flat=True)))


admin.site.register(InternalOnboardingInvite, InternalOnboardingInviteAdmin)

