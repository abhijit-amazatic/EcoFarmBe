
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
from utils import (parse_domain_from_link, )
from integration.crm import (
    get_crm_obj,
    get_records_from_crm,
    search_query,
    get_record,
    search_query,
    create_records,
    get_account_associations,
    get_vendor_associations,
    create_or_update_org_in_crm,
    get_format_dict,
)
from brand.tasks import (
    insert_record_to_crm,
)

from brand.tasks.license_oboarding_helpers import insert_data_from_crm
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
def send_internal_onboarding_invitation(invite_obj_id_list):
    """
    send organization user invitation.
    """
    qs = InternalOnboardingInvite.objects.filter(id__in=invite_obj_id_list)
    for invite_obj in qs:
        roles = [ x.name for x in invite_obj.roles.all()]
        if roles[:-1]:
            role_str = ', '.join(roles[:-1]) + ' and ' + roles[-1:][0]
        else:
            role_str = ', '.join(roles)
        context = {
            'full_name': invite_obj.user.get_full_name(),
            'email': invite_obj.user.email,
            'organization': invite_obj.organization.name,
            'roles': roles,
            'role_str': role_str,
            'license_number': invite_obj.license.license_number,
            'legal_business_name': invite_obj.license.legal_business_name,
            'phone': invite_obj.user.phone.as_e164,
            'is_new_user': invite_obj.is_user_created,
            'is_user_do_onboarding': invite_obj.is_user_do_onboarding,
        }
        f_domain = parse_domain_from_link(settings.FRONTEND_DOMAIN_NAME)
        if invite_obj.is_user_created:
            context['link'] = f'https://{f_domain}/verify-internal-onboarding-invite?token={invite_obj.get_invite_token()}'
        else:
            context['link'] = f'https://{f_domain}/login'

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
            if invite_obj.is_user_created:
                # msg = 'You have been invited to join organization "{organization}" under the license {license} as {role_str} .\nPlease check your email {email}'.format(**context)
                msg = (
                    'Your Thrive Society Account has been created under the following License: {license_number} - {legal_business_name}.\n'
                    'Please check your email {email}.'
                )
                send_sms(context['phone'], msg.format(**context))



@app.task(queue="general")
def populate_onboarding_data_to_db(user_id, license_number, license_obj_id):
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
                    insert_data_from_crm(user, response_data, license_obj_id, license_number)
                except Exception as e:
                    print('Error in insert_data_from_crm')
                    traceback.print_tb(e.__traceback__)
            else:
                print('licence_association_not_found')
        else:
            print('licence_association_not_found')
            print(response_data)



@app.task(queue="general")
def create_crm_associations(vendor_id, account_id, org_id, license_id, contacts_dict={}, constacts_data_dict={}, vendor_data={}, account_data={}):
    crm_obj = get_crm_obj()

    if vendor_id:
        r = crm_obj.update_records('Licenses', [{'id': license_id, 'Vendor_Name_Lookup': vendor_id}])
        if r.get('status_code') != 200:
            print(r)

        vendor_associations = get_vendor_associations(vendor_id=vendor_id, brands=False, cultivars=False)
        if license_id not in [x['id'] for x in vendor_associations['Licenses']]:
            r = create_records('Vendors_X_Licenses', [{'Licenses_Module': vendor_id, 'Licenses': license_id}])
            if r.get('status_code') != 201:
                print(r)
        if org_id not in [x['id'] for x in vendor_associations['Orgs']]:
            r = create_records('Orgs_X_Vendors', [{'Vendor': vendor_id, 'Org': org_id} ])
            if r.get('status_code') != 201:
                print(r)

        associated_contact = {
            x['id']: {'roles': x['roles'], 'linking_obj_id': x['linking_obj_id']}
            for x in vendor_associations['Contacts']
        }
        contact_ids_to_create_associate = [id for id in contacts_dict.keys() if id not in  associated_contact.keys()]
        if contact_ids_to_create_associate:
            create_data = [{'Vendor': vendor_id, 'Contact': x, 'Contact_Company_Role': contacts_dict[x]['roles']} for x in contact_ids_to_create_associate]
            r = create_records('Vendors_X_Contacts', create_data)
            if r.get('status_code') != 201:
                print(r)
        contact_ids_to_update_associate = [contact_id for contact_id in contacts_dict.keys() if contact_id in  associated_contact.keys()]
        if contact_ids_to_update_associate:
            update_data = [
                {'id': associated_contact[id]['linking_obj_id'], 'Contact_Company_Role': contacts_dict[id]['roles']}
                for id in contact_ids_to_update_associate
            ]
            r = crm_obj.update_records('Vendors_X_Contacts', update_data)
            if r.get('status_code') != 200:
                print(r)

    if account_id:
        r = crm_obj.update_records('Licenses', [{'id': license_id, 'Account_Name_Lookup': account_id}])
        if r.get('status_code') != 200:
            print(r)

        account_associations = get_account_associations(account_id=account_id, brands=False)
        if license_id not in [x['id'] for x in account_associations['Licenses']]:
            r = create_records('Accounts_X_Licenses', [{'Licenses_Module': account_id, 'Licenses': license_id}])
            if r.get('status_code') != 201:
                print(r)
        if org_id not in [x['id'] for x in account_associations['Orgs']]:
            r = create_records('Orgs_X_Accounts', [{'Account': account_id, 'Org': org_id}])
            if r.get('status_code') != 201:
                print(r)

        associated_contact = {
            x['id']: {'roles': x['roles'], 'linking_obj_id': x['linking_obj_id']}
            for x in account_associations['Contacts']
        }
        contact_ids_to_create_associate = [id for id in contacts_dict.keys() if id not in  associated_contact.keys()]
        if contact_ids_to_create_associate:
            create_data = [{'Accounts': account_id, 'Contacts': x, 'Contact_Company_Role': contacts_dict[x]['roles']} for x in contact_ids_to_create_associate]
            r = create_records('Accounts_X_Contacts', create_data)
            if r.get('status_code') != 201:
                print(r)
        contact_ids_to_update_associate = [contact_id for contact_id in contacts_dict.keys() if contact_id in  associated_contact.keys()]
        if contact_ids_to_update_associate:
            update_data = [
                { 'id': associated_contact[id]['linking_obj_id'], 'Contact_Company_Role': contacts_dict[id]['roles'] }
                for id in contact_ids_to_update_associate
            ]
            r = crm_obj.update_records('Accounts_X_Contacts', update_data)
            if r.get('status_code') != 200:
                print(r)

    if vendor_id and account_id:
        if vendor_data and not vendor_data.get('Associated_Account_Record'):
            r = crm_obj.update_records('Vendors', [{'id': vendor_id, 'Associated_Account_Record': account_id}])
            if r.get('status_code') != 200:
                print(r)

        if account_data and not account_data.get('Associated_Vendor_Record'):
            r = crm_obj.update_records('Accounts', [{'id': account_id, 'Associated_Vendor_Record': vendor_id}])
            if r.get('status_code') != 200:
                print(r)


@app.task(queue="general")
def create_crm_associations_and_fetch_data(create_crm_associations_kwargs, fetch_data_kwargs={}):
    create_crm_associations(**create_crm_associations_kwargs)
    populate_onboarding_data_to_db(**fetch_data_kwargs)
    insert_record_to_crm.delay(
        fetch_data_kwargs.get('license_obj_id'),
        is_update=True,
        account_crm_id=create_crm_associations_kwargs.get('account_id'),
        vendor_crm_id=create_crm_associations_kwargs.get('vendor_id'),
    )