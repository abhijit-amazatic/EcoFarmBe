import ast
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

def parse_fields(key, value, obj, crm_obj):
    """
    Parse fields
    """
    def get_dict(cd, i):
        user = dict()
        for k,v in cd.items():
            user[k] = i.get(v)
        user = create_records('Contacts', [user])
        if user['status_code'] == 201:
            return user['response']['data'][0]['details']['id']
    
    if value in ('ethics_and_certifications'):
        return ast.literal_eval(obj.get(value))
    if value.startswith('cultivars_'):
        try:
            c = value.split('_')
            d = obj.get(c[0])
            if d:
                return d[int(c[1])-1]['harvest_date']
        except Exception:
            return []
    if value.startswith('employees'):
        user = None
        d = obj.get(value)
        cd = {
            'last_name': 'employee_name',
            'email': 'employee_email',
            'phone': 'phone',
        }
        try:
            for i in d:
                if i['roles'][0] == 'Cultivation Manager' and key == 'Contact_1':
                    user = get_dict(cd, i)
                elif i['roles'][0] == 'Logistics Manager' and key == 'Contact_2':
                    user = get_dict(cd, i)
                elif i['roles'][0] == 'Quality Assurance Manager' and key == 'Contact_3':
                    user = get_dict(cd, i)
                elif i['roles'][0] == 'Owner' and key == 'Owner1':
                    user = get_dict(cd, i)
            return user
        except IndexError:
            return []
        
def create_records(module, records):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    for record in records:
        contact_dict = dict()
        contact_crm_dict = get_format_dict(module)
        for k,v in contact_crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(k, v, record, crm_obj)
                contact_dict[k] = v
            else:
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

def insert_vendors():
    """
    Insert Vendors into Zoho CRM.
    """
    data_list = list()
    records = VendorProfile.objects.filter(is_updated_in_crm=False).select_related()
    for record in records:
        r = dict()
        if record.license_set.values():
            licenses = list(record.license_set.values())
            result = create_records('Licenses', licenses)
            r.update({'licenses': [{'id': i['details']['id']} for i in result['response']['data']]})
        r.update(record.profile_contact.profile_contact_details)
        r.update(record.profile_overview.profile_overview)
        r.update(record.financial_overview.financial_details)
        r.update(record.processing_overview.processing_config)
        data_list.append(r)
    result = create_records('Vendors', data_list)
    return result