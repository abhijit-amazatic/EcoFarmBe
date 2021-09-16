from django.core import exceptions
from django.dispatch import receiver
from django.db.models import signals
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from .permission_defaults import (DEFAULT_ROLE_PERM,)
from integration.crm.crm_format import LICENSE_CULTIVATION_TYPE

Organization = apps.get_model('brand', 'Organization')
OrganizationRole = apps.get_model('brand', 'OrganizationRole')
# OrganizationUser = apps.get_model('brand', 'OrganizationUser')
# OrganizationUserRole = apps.get_model('brand', 'OrganizationUserRole')
# OrganizationUserInvite = apps.get_model('brand', 'OrganizationUserInvite')


@receiver(signals.post_save, sender=apps.get_model('brand', 'Organization'))
def post_save_user(sender, instance, created, **kwargs):
    if created:
        ###################### Add default rg roles #####################
        for role_name, perms_ls in DEFAULT_ROLE_PERM.items():
            role, _ = OrganizationRole.objects.get_or_create(
                organization=instance,
                name=role_name,
            )
            role.permissions.set(perms_ls)
            role.save()

@receiver(signals.pre_save, sender=apps.get_model('brand', 'License'))
def pre_save_license(sender, instance, **kwargs):
    if instance.license_type and not instance.cultivation_type:
        if LICENSE_CULTIVATION_TYPE.get(instance.license_type):
            instance.cultivation_type = LICENSE_CULTIVATION_TYPE.get(instance.license_type)

@receiver(signals.post_save, sender=apps.get_model('brand', 'License'))
def post_save_license(sender, instance, created, **kwargs):
    try:
        instance.binderlicense.save()
    except Exception:
        pass


@receiver(signals.pre_save, sender=apps.get_model('brand', 'LicenseProfile'))
def pre_save_license_profile(sender, instance, **kwargs):
    """
    Deletes old file.
    """
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if instance.agreement_signed and not old_instance.agreement_signed:
        try:
            instance.signed_program_name = instance.license.program_overview.program_details.get('program_name')
        except ObjectDoesNotExist:
            pass

# @receiver(signals.pre_save, sender=apps.get_model('brand', 'ProfileContact'))
# def pre_save_profile_contact(sender, instance, **kwargs):
#     """
#     Deletes old file.
#     """
#     if instance.profile_contact_details and isinstance(instance.profile_contact_details, dict):
#         try:
#             parsed_employees = dict()
#             employees = instance.profile_contact_details['employees']
#             for employee in employees:
#                 email = employee.get('employee_email')
#                 if not email in parsed_employees:
#                     parsed_employees[email] = employee
#                 else:
#                     for role in employee['roles']:
#                         if not role in parsed_employees[email]['roles']:
#                             parsed_employees[email]['roles'].append(role)
#             instance.profile_contact_details['employees'] = list(parsed_employees.values())
#         except Exception as exc:
#             print(exc)
