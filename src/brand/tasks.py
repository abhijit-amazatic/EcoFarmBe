
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
from slacker import Slacker

from integration.apps.twilio import (send_sms,)
from integration.crm import (get_format_dict, get_records_from_crm, search_query, insert_vendors, insert_accounts)
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
    send_onboarding_data_fetch_verification_mail,
)

slack = Slacker(settings.SLACK_TOKEN)

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
            if not obj.is_notified_before_expiry:    
                mail_send("license-expiry.html",{'license_number':obj.license_number,'expiration_date': obj.expiration_date.strftime('%Y-%m-%d')},"Your license will expire soon.", obj.created_by.email)   
                obj.is_notified_before_expiry = True
                obj.save()
                print('Notified License before expiry & flagged as notified',obj.license_number)

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

@app.task(queue="urgent")
def send_onboarding_data_fetch_verification(onboarding_data_fetch_id, user_id):
    """
    async task for existing user.Insert/create license based on license number.
    We use this while fetching data after first step(license creation).
    """
    instance = OnboardingDataFetch.objects.filter(id=onboarding_data_fetch_id).first()
    if instance and instance.owner_verification_status in ['not_started',]:
        response_data = search_query('Licenses', instance.license_number, 'Name', is_license=True)

        status_code = response_data.get('status_code')
        if status_code == 200:
            data = response_data.get('response', {})
            if data:
                if isinstance(data, list):
                    data = data[0]
                instance.crm_license_data = data
                instance.owner_email = data.get("License_Email")
                owner_name = data.get("Owner_First_Name","")+' '+data.get("Owner_Last_Name","")
                instance.owner_name = owner_name.strip()
                instance.legal_business_name = data.get("Legal_Business_Name")
                if instance.owner_email:
                    try:
                        send_onboarding_data_fetch_verification_mail(instance, user_id)
                    except Exception as e:
                        traceback.print_tb(e.__traceback__)
                    else:
                        instance.owner_verification_status = 'verification_code_sent'
                else:
                    instance.owner_verification_status = 'owner_email_not_found'
            else:
                instance.owner_verification_status = 'licence_data_not_found'
                instance.data_fetch_status = 'licence_data_not_found'
        elif status_code == 204:
            instance.owner_verification_status = 'licence_data_not_found'
            instance.data_fetch_status = 'licence_data_not_found'
        else:
            print(response_data)
            instance.owner_verification_status = 'error'
        instance.save()

        if instance.owner_verification_status == 'verification_code_sent':
            response_data = get_records_from_crm(license_number=instance.license_number)
            status_code = response_data.get('status_code')
            if not status_code:
                response_license_data = response_data.get(instance.license_number, {})
                if response_license_data and not response_license_data.get('error'):
                    instance.crm_profile_data = response_data
                    instance.data_fetch_status = 'fetched'
                else:
                    crm_dict = get_format_dict('Licenses_To_DB')
                    license_data = dict()
                    for k, v in crm_dict.items():
                        license_data[k] = data.get(v)
                    instance.crm_profile_data = {instance.license_number: {"license": license_data}}
                    instance.data_fetch_status = 'licence_association_not_found'

            else:
                print(response_data)
                instance.data_fetch_status = 'error'
            instance.save()


@app.task(queue="urgent")
def resend_onboarding_data_fetch_verification(onboarding_data_fetch_id, user_id):
    """
    async task for existing user.Insert/create license based on license number.
    We use this while fetching data after first step(license creation).
    """
    instance = OnboardingDataFetch.objects.filter(id=onboarding_data_fetch_id).first()
    if instance:
        status = instance.owner_verification_status
        if status == 'not_started':
            send_onboarding_data_fetch_verification(onboarding_data_fetch_id, user_id)
        if status == 'verification_code_sent' or (status == 'licence_association_not_found' and instance.email):
            try:
                send_onboarding_data_fetch_verification_mail(instance, user_id)
            except Exception as e:
                traceback.print_tb(e.__traceback__)


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
            if instance  and instance.owner_verification_status == 'verified':
                if instance.data_fetch_status == 'not_started':
                    response_data = get_records_from_crm(license_number=instance.license_number)
                    status_code = response_data.get('status_code')
                    if not status_code:
                        data = response_data.get(instance.license_number, {})
                        if data and not data.get('error'):
                            instance.crm_profile_data = response_data
                            instance.data_fetch_status = 'fetched'
                        else:
                            instance.data_fetch_status = 'licence_association_not_found'
                    else:
                        print(response_data)
                        instance.data_fetch_status = 'error'
                    instance.save()

                if instance.data_fetch_status in ('fetched', 'licence_association_not_found'):
                    try:
                        insert_data_from_crm(user, instance.crm_profile_data, license_id, instance.license_number)
                    except Exception as e:
                        print('Error in insert_data_from_crm')
                        traceback.print_tb(e.__traceback__)
                    else:
                        instance.data_fetch_status = 'complete'
                        instance.save()

@app.task(queue="urgent")
def insert_record_to_crm(record_id, is_buyer, is_seller, is_update=False):
    """
    Insert record according to buyer/seller to crm.
    """
    response = dict()
    if is_seller and is_buyer:
        response['vendor'] = insert_vendors(id=record_id, is_update=is_update)
        response['account'] = insert_accounts(id=record_id, is_update=is_update)
    elif is_seller:
        response = insert_vendors(id=record_id, is_update=is_update)
    elif is_buyer:
        response = insert_accounts(id=record_id, is_update=is_update)
    return response
