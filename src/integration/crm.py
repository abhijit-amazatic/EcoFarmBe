import ast
from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER,
    LICENSE_PARENT_FOLDER_ID)
from user.models import (User, )
from vendor.models import (VendorProfile, License, )
from account.models import (Account, )
from .crm_format import (CRM_FORMAT, VENDOR_TYPES,
                         ACCOUNT_TYPES)
from .box import (get_shared_link, move_file, create_folder)
from core.celery import app
from .utils import (get_vendor_contacts, get_account_category,
                    get_cultivars_date, )

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

def get_vendor_types(vendor_type, reverse=False):
    """
    Return Zoho CRM vendor type
    """
    response = list()
    if reverse:
        for vendor in vendor_type:
            for k,v in VENDOR_TYPES.items():
                if v == vendor:
                    response.append(k)
    else:
        for vendor in vendor_type:
            type_ = VENDOR_TYPES.get(vendor)
            if type_:
                response.append(type_)
    return response

def get_dict(cd, i):
        user = dict()
        for k,v in cd.items():
            user[k] = i.get(v)
        user = create_records('Contacts', [user])
        if user['status_code'] in (201, 202):
            return user['response']['data'][0]['details']['id']

def create_employees(key, value, obj, crm_obj):
    """
    Create contacts in Zoho CRM.
    """
    user = None
    d = obj.get(value)
    cd = {
        'last_name': 'employee_name',
        'email': 'employee_email',
        'phone': 'phone',
    }
    try:
        for i in d:
            if 'Farm Manager' in i['roles'] and key == 'Contact_1':
                user = get_dict(cd, i)
            elif 'Logistics' in i['roles'] and key == 'Contact_2':
                user = get_dict(cd, i)
            elif 'Sales/Inventory' in i['roles'] and key == 'Contact_3':
                user = get_dict(cd, i)
            elif 'License Owner' in i['roles'] and key == 'Owner1':
                user = get_dict(cd, i)
        return user
    except IndexError:
        return []

def parse_fields(key, value, obj, crm_obj):
    """
    Parse fields
    """
    def create_or_get_user(last_name, email):
        data = {}
        data['last_name'] = last_name
        data['email'] = email
        user = create_records('Contacts', [data])
        if user['status_code'] in (201, 202):
            return user['response']['data'][0]['details']['id']

    cultivator_starts_with = (
        "indoor.",
        "outdoor_full_season.",
        "outdoor_autoflower.",
        "mixed_light.",
        "po_indoor.",
        "po_outdoor_full_season.",
        "po_outdoor_autoflower.",
        "po_mixed_light.",
        "fd_indoor.",
        "fd_outdoor_full_season.",
        "fd_outdoor_autoflower.",
        "fd_mixed_light.",
    )
    if value in ('ethics_and_certifications'):
        return ast.literal_eval(obj.get(value))
    if value.startswith('po_cultivars_'):
        return get_cultivars_date(key, value, obj, crm_obj)
    if value.startswith('employees'):
        return create_employees(key, value, obj, crm_obj)
    if value == 'vendor_type':
        return get_vendor_types(obj.get(value))
    if value.startswith('Contact'):
        return get_vendor_contacts(key, value, obj, crm_obj)
    if value.startswith('layout'):
        return "4226315000000819743"
    if value.startswith('account_category'):
        return get_account_category(key, value, obj, crm_obj)
    if value.startswith('logistic_manager_email'):
        return create_or_get_user(obj.get('logistic_manager_name'), obj.get(value))
    if value.startswith('Cultivars'):
        if obj.get(value):
            return obj.get(value).split(', ')
    if value.startswith(cultivator_starts_with):
        v = value.split('.')
        data = obj.get(v[0])
        if data:
            return data.get(v[1])
        return None
    if value in ('full_season', 'autoflower'):
        return "yes" if obj.get(value) else "No"
    if value.startswith(('billing_address', 'mailing_address')):
        v = value.split('.')
        return obj.get(v[0]).get(v[1])

def create_records(module, records, is_return_orginal_data=False):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    if isinstance(records, dict):
        records = [records]
    for record in records:
        record_dict = dict()
        crm_dict = get_format_dict(module)
        for k,v in crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(k, v, record, crm_obj)
                record_dict[k] = v
            else:
                record_dict[k] = record.get(v)
        request.append(record_dict)
    response = crm_obj.insert_records(module, request, is_return_orginal_data)
    return response

def update_records(module, records, is_return_orginal_data=False):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    for record in records:
        contact_dict = dict()
        crm_dict = get_format_dict(module)
        for k,v in crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(k, v, record, crm_obj)
                contact_dict[k] = v
            else:
                contact_dict[k] = record.get(v)
        request.append(contact_dict)
    response = crm_obj.update_records(module, request, is_return_orginal_data)
    return response

def search_query(module, query, criteria, case_insensitive=False):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
    if case_insensitive:
        return crm_obj.isearch_record(module, query, criteria)
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

def get_licenses(license_field):
    """
    Get license from Zoho CRM.
    """
    licenses = search_query('Licenses', license_field, 'Legal_Business_Name')
    if licenses['status_code'] == 200:
        return licenses['response']

@app.task(queue="general")
def insert_vendors(id=None):
    """
    Insert Vendors into Zoho CRM.
    """
    data_list = list()
    if id:
        records = VendorProfile.objects.filter(id=id).select_related()
    else:
        records = VendorProfile.objects.filter(is_updated_in_crm=False).select_related()
    for record in records:
        r = dict()
        r['db_id'] = record.id
        try:
            farm_name = record.profile_contact.profile_contact_details['farm_name']
        except Exception:
            continue
        if record.license_set.values():
            l = list()
            for i in record.license_set.values():
                d = dict()
                licenses = get_licenses(i['legal_business_name'])
                d.update({'license_id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
                d.update(i)
                update_license(farm_name, d)
                l.extend(licenses)
            r.update({'licenses': l})
        try:
            type_ = record.vendor.vendor_category
            if isinstance(type_, list):
                r.update({'vendor_type': type_})
            else:
                r.update({'vendor_type': [type_]})
            r.update(record.profile_contact.profile_contact_details)
            r.update(record.profile_overview.profile_overview)
            for k,v in record.financial_overview.financial_details.items():
                r.update({'fd_' + k:v})
            for k,v in record.processing_overview.processing_config.items():
                r.update({'po_' + k:v})
            data_list.append(r)
        except Exception as exc:
            print(exc)
            continue
    if len(data_list) > 0:
        result = create_records('Vendors', data_list, True)
        if result['status_code'] == 201:
            record_response = result['response']['response']['data']
            for i, record in enumerate(data_list):
                try:
                    record_obj = VendorProfile.objects.get(id=record['db_id'])
                    record_obj.zoho_crm_id = record_response[i]['details']['id']
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError:
                    continue
                if (result['response']['orignal_data'][i].get('Licenses_List')):
                    data = dict()
                    data['Licenses_Module'] = record_response[i]['details']['id']
                    for license in result['response']['orignal_data'][i]['Licenses_List']:
                        data['Licenses'] = license
                        r = create_records('Vendors_X_Licenses', [data])
                if result['response']['orignal_data'][i].get('po_cultivars'):
                    data = dict()
                    l = list()
                    data['Cultivar_Associations'] = record_response[i]['details']['id']
                    for j in result['response']['orignal_data'][i]['po_cultivars']:
                        for k in j['cultivar_names']:
                            r = search_query('Cultivars', k, 'Name')
                            if r['status_code'] == 200:
                                data['Cultivars'] = r['response'][0]['id']
                                r = create_records('Vendors_X_Cultivars', [data])
        return result
    return {}

def update_license(farm_name, license):
    """
    Update license with shareable link.
    """
    response = None
    data = list()
    new_folder = create_folder(LICENSE_PARENT_FOLDER_ID, farm_name)
    if license.get('uploaded_license_to').isdigit():
        moved_file = move_file(license['uploaded_license_to'], new_folder)
        license_url = get_shared_link(license.get('uploaded_license_to'))
        if license_url:
            license['uploaded_license_to'] = license_url  + "?id=" + license.get('uploaded_license_to')
    if license.get('uploaded_sellers_permit_to'):
            documents = create_folder(new_folder, 'documents')
            moved_file = move_file(license['uploaded_sellers_permit_to'], documents)
            license_url = get_shared_link(license.get('uploaded_sellers_permit_to'))
            license['uploaded_sellers_permit_to'] = license_url  + "?id=" + license.get('uploaded_sellers_permit_to')
    if license.get('uploaded_w9_to'):
            documents = create_folder(new_folder, 'documents')
            moved_file = move_file(license['uploaded_w9_to'], documents)
            license_url = get_shared_link(license.get('uploaded_w9_to'))
            license['uploaded_w9_to'] = license_url + "?id=" + license.get('uploaded_w9_to')
    license_obj = License.objects.filter(pk=license['id']).update(
        uploaded_license_to=license.get('uploaded_license_to'),
        uploaded_sellers_permit_to=license.get('uploaded_sellers_permit_to'),
        uploaded_w9_to=license.get('uploaded_w9_to')
    )
    data.append(license)
    response = update_records('Licenses', data)
    return response

@app.task(queue="general")
def get_records_from_crm(legal_business_name):
    """
    Get records from Zoho CRM using legal business name.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        vendor = search_query('Vendors_X_Licenses', licenses['response'][0]['Name'], 'Licenses')
        if vendor['status_code'] != 200:
            return {}
        crm_obj = get_crm_obj()
        vendor = vendor['response'][0]['Licenses_Module']
        vendor_record = crm_obj.get_record('Vendors', vendor['id'])
        if vendor_record['status_code'] == 200:
            vendor = vendor_record['response'][vendor['id']]
            licenses = list()
            for l in vendor.get('Licenses').split(','):
                license = search_query('Licenses', l.strip(), 'Name')
                if license['status_code'] == 200:
                    licenses.append(license['response'][0])
            crm_dict = get_format_dict('Licenses_To_DB')
            li = list()
            for license in licenses:
                r = dict()
                for k, v in crm_dict.items():
                    r[k] = license.get(v)
                li.append(r)
            crm_dict = get_format_dict('Vendors_To_DB')
            response = dict()
            response['vendor_type'] = get_vendor_types(vendor['Vendor_Type'], True)
            response['licenses'] = li
            for k,v in crm_dict.items():
                r = dict()
                for key,value in v.items():
                    if value.endswith('_parse'):
                        value = value.split('_parse')[0]
                        value = parse_fields(key, value, vendor, crm_obj)
                        r[key] = value
                    else:
                        r[key] = vendor.get(value)
                response[k] = r
            return response
    return {}

def list_crm_contacts(contact_id=None):
    """
    Return contacts from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    if contact_id:
        return crm_obj.get_record('Contacts', contact_id)
    return crm_obj.get_records('Contacts')

@app.task(queue="general")
def insert_accounts(account_id=None):
    """
    Insert new accounts in Zoho CRM.
    """
    response = dict()
    request = list()
    if account_id:
        records = Account.objects.filter(id=account_id).select_related()
    else:
        records = Account.objects.filter(is_updated_in_crm=False).select_related()
    for record in records:
        try:
            req = dict()
            l = list()
            req.update(record.__dict__)
            req.update(record.account_profile.__dict__)
            req.update(record.account_contact.__dict__)
            licenses = record.account_license.all().values()
            for i in licenses:
                d = dict()
                license = get_licenses(i['legal_business_name'])
                d.update({'license_id':license[0]['id'], 'Owner':license[0]['Owner']['id']})
                d.update(i)
                update_license(req['company_name'], d)
                l.extend(license)
            req.update({'licenses': l})
        except Exception:
            continue
        request.append(req)
    if len(request) > 0:
        result = create_records('Accounts', request, is_return_orginal_data=True)
        if result['status_code'] == 201:
            record_response = result['response']['response']['data']
            for i, record in enumerate(request):
                try:
                    record_obj = Account.objects.get(id=record['id'])
                    record_obj.zoho_crm_id = record_response[i]['details']['id']
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError:
                    continue
                if (result['response']['orignal_data'][i].get('Licenses')):
                    data = dict()
                    data['Licenses_Module'] = record_response[i]['details']['id']
                    for license in result['response']['orignal_data'][i]['Licenses']:
                        data['Licenses'] = license
                        r = create_records('Accounts_X_Licenses', [data])
            return result
    return {}

@app.task(queue="general")
def get_accounts_from_crm(legal_business_name):
    """
    Fetch existing accounts from Zoho CRM.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        account = search_query('Accounts_X_Licenses', licenses['response'][0]['Name'], 'Licenses')
        if account['status_code'] != 200:
            return {}
        crm_obj = get_crm_obj()
        account = account['response'][0]['Licenses_Module']
        account_record = crm_obj.get_record('Accounts', account['id'])
        if account_record['status_code'] == 200:
            account = account_record['response'][account['id']]
            licenses = licenses['response']
            crm_dict = get_format_dict('Licenses_To_DB')
            li = list()
            for license in licenses:
                r = dict()
                for k, v in crm_dict.items():
                    r[k] = license.get(v)
                li.append(r)
            crm_dict = get_format_dict('Accounts_To_DB')
            response = dict()
            response['licenses'] = li
            for k,v in crm_dict.items():
                r = dict()
                for key,value in v.items():
                    if value.endswith('_parse'):
                        value = value.split('_parse')[0]
                        value = parse_fields(key, value, account, crm_obj)
                        r[key] = value
                    else:
                        r[key] = account.get(value)
                response[k] = r
            return response
    return {}
