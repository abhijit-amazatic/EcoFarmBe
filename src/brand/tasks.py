
"""
All periodic tasks related to brand.
"""
import datetime
from core.mailer import mail, mail_send
from django.conf import settings
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import  timezone

from integration.apps.twilio import (send_sms,)
from core.celery import app
from core.utility import (notify_admins_on_profile_user_registration,)
from user.models import (User,)
from .models import (
    License,
    ProfileContact,
    Organization,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    OrganizationUserInvite,
)


@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={'queue': 'general'})
def update_expired_licence_status():
    """
    Update expired licence status to 'expired'.
    """
    qs = License.objects.filter(expiration_date__lt=timezone.now())
    qs.update(status='expired')

@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={'queue': 'general'})
def update_before_expire():
    """
    Update/send notification to user before expiry.(now within 2 days)  
    """
    license_obj = License.objects.filter(expiration_date__range=(timezone.now().date(),timezone.now().date()+datetime.timedelta(days=7)))
    if license_obj:
        for obj in license_obj:
            if not obj.status_before_expiry:
                obj.status_before_expiry = obj.status
                obj.save()
                print('updated license before status for ',obj.license_number)
            mail_send("license-expiry.html",{'license_number':obj.license_number,'expiration_date': obj.expiration_date.strftime('%Y-%m-%d')},"Your license will expire soon.", obj.created_by.email)   


@app.task(queue="general")
def send_async_invitation(invite_obj_id):
    """
    Async send organization user invitation.
    """
    try:
        invite_obj = OrganizationUserInvite.objects.get(id=invite_obj_id)
    except OrganizationUserInvite.DoesNotExist:
        pass
    else:
        context = {
            'full_name': invite_obj.full_name,
            'email': invite_obj.email,
            'organization': invite_obj.organization.name,
            'role': invite_obj.role.name,
            'licenses': [ f"{x.license_number} | {x.legal_business_name}" for x in invite_obj.licenses.all()],
            'phone': invite_obj.phone.as_e164,
            # 'token': invite_obj.get_invite_token(),
            'link':  '{}/verify-user-invitation?code={}'.format(settings.FRONTEND_DOMAIN_NAME.rstrip('/'), invite_obj.get_invite_token()),
        }
        # context['link'] = '{}/verify-user-invitation?code={}'.format(settings.FRONTEND_DOMAIN_NAME.rstrip('/'), context['token'])

        try:
            mail_send(
                "user-invitation-mail.html",
                context,
                "Thrive Society Invitation.",
                context.get('email'),
            )
        except Exception as e:
            print(e.with_traceback)
        else:
            msg = 'You have been invited to join organization "{organization}" as {role}.\nPlease check your email {email}'.format(**context)
            send_sms(context['phone'], msg)


def extract_all_roles_from_email(email,data):
    """
    Extract all roles if same email for existing user.
    """
    final_roles = []
    for i in data:
        if i.get('employee_email') == email:
            final_roles.extend(i.get('roles'))
    return final_roles

@app.task(queue="general")
def invite_profile_contacts(profile_contact_id):
    """
    ->send invites to profile contacts
    """
    # role_map = {"License Owner":"license_owner","Farm Manager":"farm_manager","Sales/Inventory":"sales_or_inventory","Logistics":"logistics","Billing":"billing","Owner":"owner"}
    #updated_role_map  =  {"Cultivation Manager":"farm_manager","Sales Manager":"sales_or_inventory","Logistics Manager":"logistics","Billing / Accounting":"billing","Owner":"owner"}

    pro_contact_obj = ProfileContact.objects.filter(id=profile_contact_id).first()
    if pro_contact_obj:
        license_obj = pro_contact_obj.license
        employee_data = pro_contact_obj.profile_contact_details.get('employees')
        extracted_employee = [i for i in employee_data if i.get('employee_email')]
        for employee in extracted_employee:
                for role_name in employee['roles']:
                    role, _ = OrganizationRole.objects.get_or_create(
                        organization=license_obj.organization,
                        name=role_name,
                    )
                    if not license_obj.organization.created_by.email == employee['employee_email']:
                        invite = OrganizationUserInvite.objects.create(
                            full_name=employee['employee_name'],
                            email=employee['employee_email'],
                            phone=employee['phone'],
                            organization=license_obj.organization,
                            role=role,
                            created_by_id=license_obj.organization.created_by_id
                        )
                        invite.licenses.set([license_obj])
                        invite.save()
                        send_async_invitation.delay(invite.id)
                    else:
                        user = license_obj.organization.created_by
                        organization_user, _ = OrganizationUser.objects.get_or_create(
                            organization=license_obj.organization,
                            user=user,
                        )
                        organization_user_role, _ = OrganizationUserRole.objects.get_or_create(
                            organization_user=organization_user,
                            role=role,
                        )
                        organization_user_role.licenses.add(license_obj)
                        organization_user.save()

                #         notify_admins_on_profile_user_registration(obj.email,license_obj[0].license_profile.name)
                #         notify_profile_user(obj.email,license_obj[0].license_profile.name)


