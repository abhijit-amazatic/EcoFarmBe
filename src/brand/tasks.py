
"""
All periodic tasks related to brand.
"""
import datetime
import traceback
from core.mailer import mail, mail_send
from django.conf import settings
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import  timezone

from integration.apps.twilio import (send_sms,)
from integration.crm import (get_records_from_crm,)
from core.celery import app
from core.utility import (
    notify_admins_on_profile_user_registration,
)
from user.models import (User,)
from .models import (
    License,
    OnboardingDataFetch,
    ProfileContact,
    Organization,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    OrganizationUserInvite,
    OnboardingDataFetch,
)
from .task_helpers import (
    insert_data_from_crm,
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
            traceback.print_tb(e.__traceback__)
        else:
            msg = 'You have been invited to join organization "{organization}" as {role}.\nPlease check your email {email}'.format(**context)
            send_sms(context['phone'], msg)


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

                    # notify_admins_on_profile_user_registration(obj.email,license_obj[0].license_profile.name)
                    # notify_profile_user(obj.email,license_obj[0].license_profile.name)

def send_onboarding_data_fetch_verification_mail(instance, user_obj,):
    """
    docstring
    """
    if instance.status in ['not_started', 'owner_verification_sent']:
        full_name = user_obj.full_name or f'{user_obj.first_name} {user_obj.last_name}'
        context = {
            'owner_full_name':  instance.owner_name,
            'user_full_name':  full_name,
            'user_email': user_obj.email,
            'license': f"{instance.license_number} | {instance.legal_business_name}",
            'otp': instance.generate_otp_str(counter_increment=False),
        }
        try:
            mail_send(
                "license_owner_datapoputalaion_otp.html",
                context,
                "Thrive Society License Data Population verification.",
                settings.ONBOARDING_LICENSE_DATA_FETCH_OWNER_EMAIL_OVERIDE or instance.owner_email,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)
        else:
            instance.status = 'owner_verification_sent'
            instance.save()


@app.task(queue="general")
def send_onboarding_data_fetch_verification(onboarding_data_fetch_id, user_id):
    """
    async task for existing user.Insert/create license based on license number.
    We use this while fetching data after first step(license creation).
    """
    instance = OnboardingDataFetch.objects.filter(id=onboarding_data_fetch_id).first()
    if instance:
        license_number = instance.license_number
        response_data = get_records_from_crm(license_number=license_number)
        if not response_data.get('error'):
            if response_data:
                instance.crm_data = response_data
                instance.owner_email = response_data.get(license_number, {}).get("license", {}).get("Owner", {}).get("email")
                instance.owner_name = response_data.get(license_number, {}).get("license", {}).get("Owner", {}).get("name")
                instance.legal_business_name = response_data.get(license_number, {}).get("license", {}).get("legal_business_name")
                if instance.owner_email:
                    if instance.status in ['not_started', 'owner_verification_sent']:
                        try:
                            user_obj = User.objects.get(id=user_id)
                        except User.DoesNotExist:
                            pass
                        else:
                            full_name = user_obj.full_name or f'{user_obj.first_name} {user_obj.last_name}'
                            context = {
                                'owner_full_name':  instance.owner_name,
                                'user_full_name':  full_name,
                                'user_email': user_obj.email,
                                'license': f"{instance.license_number} | {instance.legal_business_name}",
                                'otp': instance.generate_otp_str(),
                            }
                            try:
                                mail_send(
                                    "license_owner_datapoputalaion_otp.html",
                                    context,
                                    "Thrive Society License Data Population verification.",
                                    settings.ONBOARDING_LICENSE_DATA_FETCH_OWNER_EMAIL_OVERIDE or instance.owner_email,
                                )
                            except Exception as e:
                                traceback.print_tb(e.__traceback__)
                            else:
                                instance.status = 'owner_verification_sent'
                                instance.save()
                else:
                    instance.status = 'owner_email_not_found'
                    instance.save()
            else:
                instance.status = 'licence_data_not_found'
                instance.save()
        else:
            print(response_data.get('error'))
            instance.status = 'licence_data_not_found'
            instance.save()

@app.task(queue="general")
def onboarding_fetched_data_insert_to_db(user_id, onboarding_data_fetch_id, license_id):
    """
    async task for existing user.Insert/create license based on license number.
    We use this while fetching data after first step(license creation).
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        pass
    else:
        try:
            instance = OnboardingDataFetch.objects.get(id=onboarding_data_fetch_id)
        except User.DoesNotExist:
            pass
        else:
            if instance  and instance.status == 'verified':
                try:
                    insert_data_from_crm(user, instance.crm_data, license_id)
                except Exception as e:
                    print('Error in insert_data_from_crm')
                    traceback.print_tb(e.__traceback__)
                else:
                    instance.status = 'complete'
                    instance.save()
