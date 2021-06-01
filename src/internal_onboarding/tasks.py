
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
from integration.crm import (get_records_from_crm, search_query, insert_vendors, insert_accounts)
from brand.task_helpers import insert_data_from_crm
from core.celery import app
from core.utility import (
    notify_admins_on_profile_user_registration,
)
from user.models import (User,)
from brand.models import (
    License,
    ProfileContact,
    Organization,
    OrganizationRole,
    OrganizationUser,
)
from .models import (
    InternalOnboardingInvite,
)

slack = Slacker(settings.SLACK_TOKEN)



@app.task(queue="general")
def send_internal_onboarding_invitation(invite_obj_id):
    """
    send organization user invitation.
    """
    try:
        invite_obj = InternalOnboardingInvite.objects.get(id=invite_obj_id)
    except InternalOnboardingInvite.DoesNotExist:
        pass
    else:
        roles = [ x.name for x in invite_obj.roles.all()]
        if roles[:-1]:
            role_str = ', '.join(roles[:-1]) + ' and ' + roles[:-1]
        else:
            role_str = ', '.join(roles)
        context = {
            'full_name': invite_obj.user.get_full_name(),
            'email': invite_obj.user.email,
            'organization': invite_obj.organization.name,
            'roles': roles,
            'role_str': role_str,
            'license': f"{invite_obj.license.legal_business_name} - {invite_obj.license.license_number}",
            'phone': invite_obj.user.phone.as_e164,
            # 'token': invite_obj.get_invite_token(),
            'link':  '{}/verify-onboarding-invitation?token={}'.format(settings.FRONTEND_DOMAIN_NAME.rstrip('/'), invite_obj.get_invite_token()),
        }
        # context['link'] = '{}/verify-user-invitation?code={}'.format(settings.FRONTEND_DOMAIN_NAME.rstrip('/'), context['token'])

        try:
            mail_send(
                "email/internal-onboarding-invite.html",
                context,
                "Thrive Society Invitation.",
                context.get('email'),
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)
        else:
            # msg = 'You have been invited to join organization "{organization}" under the license {license} as {role_str} .\nPlease check your email {email}'.format(**context)
            msg = (
                'Your Thrive Society Account has been created under the following License: {license}.\n'
                'Please check your email {email}'
            )
            send_sms(context['phone'], msg.format(**context))



# @app.task(queue="urgent")
# def send_onboarding_data_fetch_verification(license_id, user_id):
#     """
#     async task for existing user.Insert/create license based on license number.
#     We use this while fetching data after first step(license creation).
#     """
#     instance = License.objects.filter(id=license_id).first()
#     response_data = search_query('Licenses', instance.license_number, 'Name', is_license=True)
#     status_code = response_data.get('status_code')
#     if status_code == 200:
#         data = response_data.get('response', {})
#         if data:
#             if isinstance(data, list):
#                 data = data[0]
#             instance.crm_license_data = data
#             instance.owner_email = data.get("License_Email")
#             owner_name = data.get("Owner_First_Name","")+' '+data.get("Owner_Last_Name","")
#             instance.owner_name = owner_name.strip()
#             instance.legal_business_name = data.get("Legal_Business_Name")
#             if instance.owner_email:
#                 pass
#                 # try:
#                 #     send_onboarding_data_fetch_verification_mail(instance, user_id)
#                 # except Exception as e:
#                 #     traceback.print_tb(e.__traceback__)
#                 else:
#                     instance.owner_verification_status = 'verification_code_sent'
#             else:
#                 instance.owner_verification_status = 'owner_email_not_found'
#         else:
#             instance.owner_verification_status = 'licence_data_not_found'
#             instance.data_fetch_status = 'licence_data_not_found'
#     elif status_code == 204:
#         instance.owner_verification_status = 'licence_data_not_found'
#         instance.data_fetch_status = 'licence_data_not_found'
#     else:
#         print(response_data)
#         instance.owner_verification_status = 'error'
#     instance.save()
#     if instance.owner_verification_status == 'verification_code_sent':
#         response_data = get_records_from_crm(license_number=instance.license_number)
#         status_code = response_data.get('status_code')
#         if not status_code:
#             data = response_data.get(instance.license_number, {})
#             if data and not data.get('error'):
#                 instance.crm_profile_data = response_data
#                 instance.data_fetch_status = 'fetched'
#             else:
#                 instance.data_fetch_status = 'licence_association_not_found'
#         else:
#             print(response_data)
#             instance.data_fetch_status = 'error'
#         instance.save()




@app.task(queue="general")
def fetch_onboarding_data_to_db(user_id, license_number, license_id):
    """
    async task for existing user.Insert/create license based on license number.
    We use this while fetching data after first step(license creation).
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as e:
        traceback.print_tb(e.__traceback__)
    else:

        response_data = get_records_from_crm(license_number=license_number)
        status_code = response_data.get('status_code')
        if not status_code:
            data = response_data.get(license_number, {})
            if data and not data.get('error'):
                try:
                    insert_data_from_crm(user, response_data, license_id, license_number)
                except Exception as e:
                    print('Error in insert_data_from_crm')
                    traceback.print_tb(e.__traceback__)
            else:
                print('licence_association_not_found')
        else:
            print('licence_association_not_found')
            print(response_data)


