from integration.crm import (search_query, get_users,)
from django.contrib.auth import get_user_model

User = get_user_model()

def fetch_and_update_crm_user_id():
    try:
        result = get_users(user_type='ActiveUsers')
        if result.get('status_code') == 200:
            crm_email_id_map = {user.get('email'): user.get('id') for user in result.get('response', [])}
            if crm_email_id_map:
                users = list(User.objects.filter(email__in=crm_email_id_map.keys()))
                if users:
                    for user in users:
                        user.zoho_crm_id = crm_email_id_map.get(user.email)
                    User.objects.bulk_update(users, ['zoho_crm_id'])
        else:
            print(result)
    except Exception as exc:
        print(exc)


def get_user_owned_accounts_crm_id(crm_user_id):
    if crm_user_id:
        result = search_query('Accounts', crm_user_id, 'Owner')
        if result.get('status_code') == 200:
            data_ls = result.get('response')
            if data_ls and isinstance(data_ls, list):
                return [x.get('id') for x in data_ls if x.get('id')]
    return []


def get_user_owned_vendors_crm_id(crm_user_id):
    if crm_user_id:
        result = search_query('Vendors', crm_user_id, 'Owner')
        if result.get('status_code') == 200:
            data_ls = result.get('response')
            if data_ls and isinstance(data_ls, list):
                return [x.get('id') for x in data_ls if x.get('id')]
    return []


def get_user_owned_profiles_crm_id(user_id):
    fetch_and_update_crm_user_id()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return []
    else:
        if user.zoho_crm_id:
            return get_user_owned_accounts_crm_id(user.zoho_crm_id) + get_user_owned_vendors_crm_id(user.zoho_crm_id)
        else:
            return []
