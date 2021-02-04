from django.dispatch import receiver
from django.db.models import signals
from django.apps import apps

from brand.utils import get_unique_org_name
from core.utility import (send_verification_link_user_instance,)

PrimaryPhoneTOTPDevice = apps.get_model('user', 'PrimaryPhoneTOTPDevice')
Organization = apps.get_model('brand', 'Organization')
OrganizationUser = apps.get_model('brand', 'OrganizationUser')
OrganizationUserRole = apps.get_model('brand', 'OrganizationUserRole')
OrganizationUserInvite = apps.get_model('brand', 'OrganizationUserInvite')


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
        ################### add default org ###################
        Organization.objects.get_or_create(
            name=get_unique_org_name(Organization),
            created_by=instance,
        )

        ###################### user invite #####################
        invites = OrganizationUserInvite.objects.filter(
            email=instance.email,
            status='accepted',
        )
        for invite in invites:
            organization_user = OrganizationUser.objects.get_or_create(
                organization=invite.organization,
                user=instance,
            )
            organization_user_role = OrganizationUserRole.objects.get(
                organization_user=organization_user,
                role=invite.role,
            )
            organization_user_role.licenses.add(*invite.licenses.all())
            invite.status = 'completed'
            invite.save()