from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER)
from user.models import (User, )
from vendor.models import (VendorProfile, )
from .crm_format import (CRM_FORMAT, )


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
            
 
def get_format_dict(module):
    """
    Return Contact-CRM fields dictionary.
    """
    return CRM_FORMAT[module]

def create_records(module, records):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    for record in records:
        print(record)
        print('--------------------')
        contact_dict = dict()
        contact_crm_dict = get_format_dict(module)
        for k,v in contact_crm_dict.items():
            contact_dict[k] = record.get(v)
        request.append(contact_dict)
        print(request)
    #response = crm_obj.insert_records(module, request)
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

def insert_vendors():
    """
    Insert Vendors into Zoho CRM.
    """
    data_list = list()
    records = VendorProfile.objects.filter(is_updated_in_crm=False).select_related()
    for record in records:
        r = dict()
        r.update(record.profile_contact.profile_contact_details)
        r.update(record.profile_overview.profile_overview)
        r.update(record.financial_overview.financial_details)
        r.update(record.processing_overview.processing_config)
        data_list.append(r)
    result = create_records('Vendors', data_list)
    return result