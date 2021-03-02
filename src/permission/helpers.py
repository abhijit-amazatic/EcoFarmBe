from integration.crm import (search_query, get_users,)


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


def get_user_owned_profiles_crm_id(email):
    if email:
        try:
            result = get_users(user_type='ActiveUsers')
            if result.get('status_code') == 200:
                for user in result.get('response'):
                    if user['email'] == email:
                        crm_user_id = user.get('id')
                        if crm_user_id:
                            return get_user_owned_accounts_crm_id(crm_user_id) + get_user_owned_vendors_crm_id(crm_user_id)
            else:
                print(result)
        except Exception as exc:
            print(exc)
    return []
