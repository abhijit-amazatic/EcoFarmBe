from django.dispatch import receiver
from django.db.models import signals
from django.apps import apps

from brand.utils import get_unique_org_name
from core.utility import (send_verification_link_user_instance,)

PrimaryPhoneTOTPDevice = apps.get_model('user', 'PrimaryPhoneTOTPDevice')
Organization = apps.get_model('brand', 'Organization')
OrganizationUser = apps.get_model('brand', 'OrganizationUser')
OrganizationUserRole = apps.get_model('brand', 'OrganizationUserRole')
LicenseUserInvite = apps.get_model('brand', 'LicenseUserInvite')


@receiver(signals.pre_save, sender=apps.get_model('user', 'User'))
def pre_save_user(sender, instance, **kwargs):
    """
    Deletes old file.
    """
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if not instance.phone == old_instance.phone:
        instance.is_phone_verified = False
    if not instance.email.lower() == old_instance.email.lower():
        instance.is_verified = False
        send_verification_link_user_instance(instance)


@receiver(signals.post_save, sender=apps.get_model('user', 'User'))
def post_save_user(sender, instance, created, **kwargs):
    try:
        instance.primary_phone_totp_device
    except sender.primary_phone_totp_device.RelatedObjectDoesNotExist:
        PrimaryPhoneTOTPDevice.objects.create(user=instance)

    if created:
        ###################### user invite #####################
        invites = LicenseUserInvite.objects.filter(
            email__iexact=instance.email,
            status__in=['pending', 'user_joining_platform']
        )
        for invite in invites:
            if invite.is_invite_accepted:
                organization_user, _ = OrganizationUser.objects.get_or_create(
                    organization=invite.license.organization,
                    user=instance,
                )
                for role in invite.roles.all():
                    organization_user_role, _ = OrganizationUserRole.objects.get_or_create(
                        organization_user=organization_user,
                        role=role,
                    )
                    organization_user_role.licenses.add(invite.license)
                invite.status = 'completed'
                invite.save()
            elif invite.status == 'user_joining_platform':
                invite.status = 'pending'
                invite.save()