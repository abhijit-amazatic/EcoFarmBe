from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER)
from user.models import (User, )


def get_crm_obj():
    """
    Return ZCRM object.
    """
    return CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)

def get_picklist(module, field_name):
    """
    Return picklist for field.
    """
    crm_obj = get_crm_obj()
    module = crm_obj.get_module(module)['response']
    fields = module.get_all_fields().response_json['fields']
    for field in fields:
        if field['field_label'] == field_name and field['data_type'] in ('picklist', 'multiselectpicklist'):
            return field['pick_list_values']
    return list()
            
 
def get_contact_dict():
    """
    Return Contact-CRM fields dictionary.
    """
    #key- field from CRM, value- field from user model.
    return {
        'Email': 'email',
        'First_Name': 'first_name',
        'Last_Name': 'last_name',
        'Full_Name': 'full_name',
        'Other_Country': 'country',
        'Other_State': 'state',
        'Date_Of_Birth': 'date_of_birth',
        'Other_City': 'city',
        'Other_Zip': 'zip_code',
        'Phone': 'phone'
    }

def create_records(module, records):
    crm_obj = get_crm_obj()
    request = list()
    for record in records:
        contact_dict = dict()
        contact_crm_dict = get_contact_dict()
        for k,v in contact_crm_dict.items():
            contact_dict[k] = record.get(v)
        request.append(contact_dict)
    response = crm_obj.insert_records(module, request)
    return response

def search_query(module, query, criteria):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
    return crm_obj.search_record(module, query, criteria)

def insert_users():
    """
    Insert Users in Zoho CRM.
    """
    records = User.objects.filter(is_updated_in_crm=False, existing_member=False)
    if not records:
        return {'status': 'QuerySet empty. No records to push.'}
    response = create_records('Contacts', records.values())
    if response['status_code'] == 201:
        response = response['response']['data']
        for idx, record in enumerate(records):
            record.zoho_contact_id = response[idx]['details']['id']
            record.is_updated_in_crm = True
            record.save()
        return response
    else:
        return response