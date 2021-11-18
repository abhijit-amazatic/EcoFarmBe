
"""
All periodic tasks related to brand.
"""
import traceback
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import  timezone

from slacker import Slacker

from integration.apps.twilio import (send_sms,)
from integration.books import (
    get_books_obj,
    search_contact,
)
from integration.crm import (
    get_format_dict,
    get_records_from_crm,
    search_query,
)
from core.celery import app
from user.models import (User,)
from ..models import (
    License,
    OnboardingDataFetch,
    ProfileContact,
    Organization,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
    OnboardingDataFetch,
    LicenseUserInvite,
)
from .license_oboarding_helpers import (
    insert_data_from_crm,
    send_license_onboarding_verification_mail,
)

slack = Slacker(settings.SLACK_TOKEN)


@app.task(queue="urgent")
def send_license_onboarding_verification_task(onboarding_data_fetch_id, user_id):
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
                f_name = data.get("Owner_First_Name") or ""
                l_name = data.get("Owner_Last_Name") or ""
                owner_name = f_name + ' ' + l_name
                instance.owner_name = owner_name.strip()
                instance.legal_business_name = data.get("Legal_Business_Name")
                if instance.owner_email:
                    try:
                        send_license_onboarding_verification_mail(instance, user_id)
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
def resend_license_onboarding_verification_task(onboarding_data_fetch_id, user_id):
    """
    async task for existing user.Insert/create license based on license number.
    We use this while fetching data after first step(license creation).
    """
    instance = OnboardingDataFetch.objects.filter(id=onboarding_data_fetch_id).first()
    if instance:
        status = instance.owner_verification_status
        if status == 'not_started':
            send_license_onboarding_verification_task(onboarding_data_fetch_id, user_id)
        if status == 'verification_code_sent' or (status == 'licence_association_not_found' and instance.email):
            try:
                send_license_onboarding_verification_mail(instance, user_id)
            except Exception as e:
                traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def onboarding_verified_license_data_population_task(user_id, onboarding_data_fetch_id, license_id):
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

