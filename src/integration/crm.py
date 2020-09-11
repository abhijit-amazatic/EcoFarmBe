import ast
import json
from datetime import (datetime, timedelta, )
from urllib.parse import (unquote, )
from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER,
    LICENSE_PARENT_FOLDER_ID)
from user.models import (User, )
from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from .crm_format import (CRM_FORMAT, VENDOR_TYPES,
                         ACCOUNT_TYPES)
from .box import (get_shared_link, move_file, create_folder)
from core.celery import app
from .utils import (get_vendor_contacts, get_account_category,
                    get_cultivars_date, get_layout,)
from core.mailer import mail, mail_send
from brand.models import (Brand, License, LicenseProfile, )

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
    picklist_types = ('picklist', 'multiselectpicklist', 'pick_list_values', )
    crm_obj = get_crm_obj()
    module = crm_obj.get_module(module)
    if module.get('response'):
        module = module['response']
        fields = module.get_all_fields().response_json['fields']
        for field in fields:
            if field['field_label'] == field_name and field['data_type'] in picklist_types:
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
    except TypeError:
        return []

def parse_fields(module, key, value, obj, crm_obj):
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
        "co.",
        "fo.",
        "cr.",
    )
    fields = (
        'co_.canopy_sqf',
        'co_.no_of_harvest',
        'co_.plants_per_cycle',
    )
    if value.startswith('ethics_and_certification'):
        if isinstance(obj.get(value), list) and len(obj.get(value)) > 0:
            return obj.get(value)
        return []
    if value.startswith('program_details'):
        d = obj.get('program_details')
        if len(d) > 0:
            return d.get('program_name')
    if value.startswith('employees'):
        return create_employees(key, value, obj, crm_obj)
    if value == 'brand_category':
        return get_vendor_types(obj.get(value))
    if value.startswith('Contact'):
        return get_vendor_contacts(key, value, obj, crm_obj)
    if value.startswith('layout'):
        layout_name = obj.get('Layout_Name')
        return get_layout(module, layout_name)
    if value.startswith('account_category'):
        return get_account_category(key, value, obj, crm_obj)
    if value.startswith('logistic_manager_email'):
        if obj.get('logistic_manager_name'):
            return create_or_get_user(obj.get('logistic_manager_name'), obj.get(value))
    if value.startswith('Cultivars'):
        if obj.get(value):
            return obj.get(value).split(', ')
    list_fields = (
        'transportation_methods',
        'cultivation_type',
        'vendor_type',
        'type_of_nutrients'
        )
    if value.startswith(list_fields):
        if isinstance(obj.get(value), list):
            return obj.get(value)
        return []
    boolean_conversion_list = ('issues_with_failed_labtest', 'cr.process_on_site', 'transportation')
    if value.startswith(boolean_conversion_list):
        return 'Yes' if obj.get(value) in [True, 'true', 'True'] else 'No'
    boolean_conversion_list = ('featured_on_our_site',)
    if value.startswith(boolean_conversion_list):
        return True if obj.get(value) in ['true', 'True'] else False
    elif value.startswith(cultivator_starts_with) and (value not in fields):
        v = value.split('.')
        for i in ['.mixed_light', '.indoor', '.outdoor_full_season', '.outdoor_autoflower']:
            d = obj.get(v[0] + i)
            if d:
                if 'cultivars' in v[1]:
                    return get_cultivars_date(key, v[1], d, crm_obj)
                return d.get(v[1])
        return None
    elif value in fields:
        v = value.split('_.')
        for i in ['.mixed_light', '.indoor', '.outdoor_full_season', '.outdoor_autoflower']:
            d = obj.get(v[0] + i)
            if isinstance(d, dict) and len(d)>0:
                return d.get(v[1])
        return None
    if value in ('full_season', 'autoflower'):
        return "yes" if obj.get(value) else "No"
    if value.startswith(('billing_address', 'mailing_address')):
        v = value.split('.')
        if len(v) == 2 and obj.get(v[0]):
            return obj.get(v[0]).get(v[1])
    if value.startswith('po_cultivars'):
        cultivars = list()
        for i in ['po_mixed_light', 'po_outdoor_autoflower', 'po_outdoor_full_season', 'po_indoor']:
            for cultivar in obj.get(i)['cultivars']:
                cultivars.extend(cultivar['cultivar_names'])
        return cultivars
    
def get_record(module, record_id, full=False):
    """
    Get record.
    """
    crm_obj = get_crm_obj()
    if full:
        return crm_obj.get_full_record(module, record_id)
    return crm_obj.get_record(module, record_id)

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
                v = parse_fields(module, k, v, record, crm_obj)
                record_dict[k] = v
            else:
                v = record.get(v)
                record_dict[k] = v
        request.append(record_dict)
    response = crm_obj.insert_records(module, request, is_return_orginal_data)
    return response

def update_records(module, records, is_return_orginal_data=False):
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
                v = parse_fields(module, k, v, record, crm_obj)
                record_dict[k] = v
            else:
                record_dict[k] = record.get(v)
        request.append(record_dict)
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

def insert_record(record=None, is_update=False, id=None, is_single_user=False):
    """
    Insert record to Zoho CRM.
    """
    if id and is_single_user:
        licenses = [License.objects.select_related().get(id=id).__dict__]
    else:
        licenses = record.license_set.values()
    final = list()
    for i in licenses:
        try:
            d = dict()
            l = list()
            d.update(i)
            license_db_id= i['id']
            d.update({'license_db_id': license_db_id})
            license_db = License.objects.select_related().get(id=license_db_id)
            licenses = get_licenses(i['legal_business_name'])
            d.update(license_db.license_profile.__dict__)
            d.update(license_db.profile_contact.profile_contact_details)
            vendor_id = license_db.profile_contact.__dict__['id']
            try:
                for k, v in license_db.cultivation_overview.__dict__.items():
                    d.update({'co.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db.financial_overview.__dict__.items():
                    d.update({'fo.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db.crop_overview.__dict__.items():
                    d.update({'cr.' + k:v})
            except Exception:
                pass
            d.update(license_db.program_overview.__dict__)
            d.update({'license_id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
            l.append(d['license_id'])
            d.update({'licenses': l})
            if record and is_update:
                d['id'] = record.zoho_crm_id
            elif id and is_single_user and is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
            if is_single_user:
                brand_name = license_db.license_profile.__dict__['name']
            else:
                brand_name = record.brand_name
            response = update_license(brand_name, d)
            if response['status_code'] == 200:
                    record_response = response['response']['data']
                    try:
                        record_obj = License.objects.get(id=license_db_id)
                        record_obj.zoho_crm_id = record_response[0]['details']['id']
                        record_obj.is_updated_in_crm = True
                        record_obj.save()
                    except KeyError as exc:
                        print(exc)
                        continue
            if is_update:
                result = update_records('Vendors', d, True)
            else:
                result = create_records('Vendors', d, True)
            if response['status_code'] == 200 and result['status_code'] == 201:
                record_response = result['response']['response']['data']
                try:
                    record_obj = LicenseProfile.objects.get(id=vendor_id)
                    record_obj.zoho_crm_id = record_response[0]['details']['id']
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
                    continue
                if (result['response']['orignal_data'][0].get('Licenses_List')):
                    data = dict()
                    data['Licenses_Module'] = record_response[0]['details']['id']
                    for license in result['response']['orignal_data'][0]['Licenses_List']:
                        data['Licenses'] = license
                        r = create_records('Vendors_X_Licenses', [data])
                if result['response']['orignal_data'][0].get('po_cultivars'):
                    data = dict()
                    l = list()
                    data['Cultivar_Associations'] = record_response[0]['details']['id']
                    for j in result['response']['orignal_data'][0]['po_cultivars']:
                            r = search_query('Cultivars', j, 'Name')
                            if r['status_code'] == 200:
                                data['Cultivars'] = r['response'][0]['id']
                                r = create_records('Vendors_X_Cultivars', [data])
                final.append(result)
        except Exception as exc:
            print(exc)
    return final
            
@app.task(queue="general")
def insert_vendors(id=None, is_update=False, is_single_user=False):
    """
    Insert Vendors into Zoho CRM.
    """
    if is_single_user:
        return insert_record(id=id, is_update=is_update, is_single_user=is_single_user)
    else:
        if id:
            records = Brand.objects.filter(id=id)
        else:
            records = Brand.objects.filter(is_updated_in_crm=False)
        for record in records:
            if is_update:
                record.id = record.zoho_crm_id
                result = update_records('Brands', record.__dict__, True)
            else:
                result = create_records('Brands', record.__dict__, True)
            if result['status_code'] == 201:
                try:
                    record_obj = Brand.objects.get(id=id)
                    record_obj.zoho_crm_id = result['response']['response']['data'][0]['details']['id']
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
                    continue
            record_response = insert_record(record=record, is_update=is_update)
            for i in range(len(record_response)):
                if result['status_code'] == 201 and record_response[i]['status_code'] == 201:
                    data = dict()
                    resp_brand = result['response']['response']['data']
                    resp_vendor = record_response[i]['response']['response']['data']
                    data['name'] = result['response']['orignal_data'][0]['Name'] + '_' +\
                        record_response[i]['response']['orignal_data'][0]['Vendor_Name']
                    data['brands'] = resp_brand[0]['details']['id']
                    data['vendors'] = resp_vendor[0]['details']['id']
                    if is_update:
                        r = update_records('Brands_X_Vendors', [data])
                    else:
                        r = create_records('Brands_X_Vendors', [data])
            return record_response
        return []

def update_license(name, license):
    """
    Update license with shareable link.
    """
    response = None
    data = list()
    new_folder = create_folder(LICENSE_PARENT_FOLDER_ID,name)
    if license.get('uploaded_license_to') and license.get('uploaded_license_to').isdigit():
        moved_file = move_file(license['uploaded_license_to'], new_folder)
        license_url = get_shared_link(license.get('uploaded_license_to'))
        if license_url:
            license['uploaded_license_to'] = license_url  + "?id=" + license.get('uploaded_license_to')
    if license.get('uploaded_sellers_permit_to') and license.get('uploaded_sellers_permit_to').isdigit():
            documents = create_folder(new_folder, 'documents')
            moved_file = move_file(license['uploaded_sellers_permit_to'], documents)
            license_url = get_shared_link(license.get('uploaded_sellers_permit_to'))
            license['uploaded_sellers_permit_to'] = license_url  + "?id=" + license.get('uploaded_sellers_permit_to')
    if license.get('uploaded_w9_to') and license.get('uploaded_w9_to').isdigit():
            documents = create_folder(new_folder, 'documents')
            moved_file = move_file(license['uploaded_w9_to'], documents)
            license_url = get_shared_link(license.get('uploaded_w9_to'))
            license['uploaded_w9_to'] = license_url + "?id=" + license.get('uploaded_w9_to')
    license_obj = License.objects.filter(pk=license['license_db_id']).update(
        uploaded_license_to=license.get('uploaded_license_to'),
        uploaded_sellers_permit_to=license.get('uploaded_sellers_permit_to'),
        uploaded_w9_to=license.get('uploaded_w9_to')
    )
    data.append(license)
    response = update_records('Licenses', data)
    return response

def get_vendors_from_licenses(field, licenses):
    """
    Get vendor id from licenses.
    """
    for license in licenses['response']:
        vendor_lookup = license.get(field)
        if vendor_lookup:
            return vendor_lookup.get('id')

@app.task(queue="general")
def get_records_from_crm(legal_business_name):
    """
    Get records from Zoho CRM using legal business name.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        license_number = licenses['response'][0]['Name']
        vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
        if vendor['status_code'] != 200:
            vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', licenses)
        else:
            vendor = vendor['response'][0]['Licenses_Module']
            vendor_id = vendor['id']
        if not vendor_id:
            return {'error': 'No association found for legal business name'}
        crm_obj = get_crm_obj()
        vendor_record = crm_obj.get_record('Vendors', vendor_id)
        if vendor_record['status_code'] == 200:
            vendor = vendor_record['response'][vendor_id]
            licenses = [licenses['response'][0]]
            if vendor.get('Licenses'):
                license_list = vendor.get('Licenses').split(',')
                license_list.remove(license_number  )
                for l in license_list:
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
                        value = parse_fields('Vendors', key, value, vendor, crm_obj)
                        r[key] = value
                    else:
                        r[key] = vendor.get(value)
                response[k] = r
            return response
    return {}

def get_vendor_from_contact(contact_email):
    """
    Return vendor information using contact email.
    """
    response = dict()
    contact_details = search_query('Contacts', contact_email, 'Email')
    if contact_details['status_code'] == 200:
        response['contact_company_role'] = contact_details['response'][0]['Contact_Company_Role']
        vendor_details = search_query(
            'Vendors_X_Contacts',
            contact_details['response'][0]['id'],
            'Contact')
        if vendor_details['status_code'] == 200:
            vendor_id = vendor_details['response'][0]['Vendor']['id']
            response['vendor'] = get_record('Vendors', vendor_id)['response']
            response['code'] = 0
            return response
    return {'code': 1, 'error': 'No data found'}

def list_crm_contacts(contact_id=None):
    """
    Return contacts from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    if contact_id:
        return crm_obj.get_record('Contacts', contact_id)
    return crm_obj.get_records('Contacts')

def insert_account_record(record=None, is_update=False, id=None, is_single_user=False):
    """
    Insert account to Zoho CRM.
    """
    if is_single_user:
        licenses = [License.objects.select_related().get(id=id).__dict__]
    else:
        licenses = record.license_set.values()
    for i in licenses:
        l = list()
        d = dict()
        d.update(i)
        license_db_id= i['id']
        license_db = License.objects.select_related().get(id=license_db_id)
        licenses = get_licenses(i['legal_business_name'])
        d.update(license_db.license_profile.__dict__)
        d.update(license_db.profile_contact.__dict__)
        vendor_id = license_db.profile_contact.__dict__['id']
        for k, v in license_db.cultivation_overview.__dict__.items():
            d.update({'co.' + k:v})
        for k, v in license_db.financial_overview.__dict__.items():
            d.update({'fo.' + k:v})
        for k, v in license_db.crop_overview.__dict__.items():
            d.update({'cr.' + k:v})
        d.update(license_db.program_overview.__dict__)
        d.update({'license_id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
        l.append(d['license_id'])
        d.update({'licenses': l})    
        if record and is_update:
            d['id'] = record.zoho_crm_id
        elif id and is_single_user and is_update:
            d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
        if is_single_user:
            brand_name = license_db.license_profile.__dict__['name']
        else:
            brand_name = record.brand_name
        response = update_license(brand_name, d)
        if response['status_code'] == 200:
            record_response = response['response']['data']
            try:
                record_obj = License.objects.get(id=license_db_id)
                # record_obj.zoho_crm_id = record_response[0]['details']['id']
                # record_obj.is_updated_in_crm = True
                # record_obj.save()
            except KeyError as exc:
                print(exc)
        if is_update:
            result = update_records('Accounts', d, is_return_orginal_data=True)
        else:    
            result = create_records('Accounts', d, is_return_orginal_data=True)
        if response['status_code'] == 200 and result['status_code'] == 201:
            record_response = result['response']['response']['data']
            try:
                record_obj = LicenseProfile.objects.get(id=vendor_id)
                # record_obj.zoho_crm_id = record_response[i]['details']['id']
                # record_obj.is_updated_in_crm = True
                # record_obj.save()
            except KeyError:
                continue
            if (result['response']['orignal_data'][0].get('Licenses_List')):
                data = dict()
                data['Licenses_Module'] = record_response[0]['details']['id']
                for license in result['response']['orignal_data'][0]['Licenses_List']:
                    data['Licenses'] = license
                    if is_update:
                        r = update_records('Accounts_X_Licenses', [data])
                    else:
                        r = create_records('Accounts_X_Licenses', [data])
        return result

@app.task(queue="general")
def insert_accounts(id=None, is_update=False, is_single_user=False):
    """
    Insert new accounts in Zoho CRM.
    """
    if is_single_user:
        return insert_account_record(id=id, is_single_user=is_single_user)
    else:
        response = list()
        if id:
            records = Brand.objects.filter(id=id).select_related()
        else:
            records = Brand.objects.filter(is_updated_in_crm=False).select_related()
        for record in records:
            try:
                if is_update:
                    result = update_records('Brands', records.__dict__, True)
                else:
                    result = create_records('Brands', records.__dict__, True)
                if result['status_code'] == 201:
                    try:
                        record_obj = Brand.objects.get(id=id)
                        # record_obj.zoho_crm_id = result['response']['response']['data'][0]['details']['id']
                        # record_obj.is_updated_in_crm = True
                        # record_obj.save()
                    except KeyError as exc:
                        print(exc)
                        continue
                record_response = insert_account_record(record=record, is_update=is_update)
                if result['status_code'] == 201 and record_response['status_code'] == 201:
                    data = dict()
                    resp_brand = result['response']['response']['data']
                    resp_vendor = record_response['response']['response']['data']
                    data['brands'] = resp_brand[0]['details']['id']
                    data['accounts'] = resp_vendor[0]['details']['id']
                    if is_update:
                        r = update_records('Brands_X_Accounts', [data])
                    else:
                        r = create_records('Brands_X_Accounts', [data])
                response.append(record_response)
            except Exception as exc:
                print(exc)
                continue
        return response

@app.task(queue="general")
def get_accounts_from_crm(legal_business_name):
    """
    Fetch existing accounts from Zoho CRM.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        license_number = licenses['response'][0]['Name']
        account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
        if account['status_code'] != 200:
            account_id = get_vendors_from_licenses('Account_Name_Lookup', licenses)
        else:
            account = account['response'][0]['Licenses_Module']
            account_id = account['id']
        if not account_id:
            return {'error': 'No association found for legal business name'}
        crm_obj = get_crm_obj()
        account_record = crm_obj.get_record('Accounts', account_id)
        if account_record['status_code'] == 200:
            account = account_record['response'][account_id]
            licenses = [licenses['response'][0]]
            if account.get('Licenses'):
                license_list = account.get('Licenses').split(',')
                license_list.remove(license_number)
                for l in license_list:
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
            crm_dict = get_format_dict('Accounts_To_DB')
            response = dict()
            response['licenses'] = li
            for k,v in crm_dict.items():
                r = dict()
                for key,value in v.items():
                    if value.endswith('_parse'):
                        value = value.split('_parse')[0]
                        value = parse_fields('Accounts', key, value, account, crm_obj)
                        r[key] = value
                    else:
                        r[key] = account.get(value)
                response[k] = r
            return response
    return {}

@app.task(queue="general")
def create_lead(record):
    """
    Create lead in Zoho CRM.
    """
    response = create_records('Leads', record)
    mail_send("connect.html",{'first_name': record.get("first_name"),'last_name':record.get("last_name"),'mail':record.get("email"),'company_name':record.get("company_name"),'title':record.get("title"),'vendor_category':','.join(record.get("vendor_category")),'heard_from':record.get("heard_from"),'phone':record.get("phone"),'message':record.get("message")},"New lead via connect page.",'connect@thrive-society.com')
    return response

def get_field(record, key, field):
    """
    Parse crm fields.
    """
    date_fields = [
        'Date_Harvested',
        'Date_Received',
        'Date_Reported',
        'Date_Tested',
        'Created_Time',
        'Last_Activity_Time',
        'Modified_Time',
    ]
    if field in ('created_by', 'modified_by'):
        return record.get(key).get('id')
    if field in ('parent_1', 'parent_2'):
        return [record.get(key).get('id')]
    if field in date_fields:
        return datetime.strptime(record.get(key), '%Y-%m-%d')

def parse_crm_record(module, records):
    """
    Parse crm record.
    """
    record_list = list()
    crm_obj = get_crm_obj()
    crm_dict = get_format_dict(module)
    for record in records:
        record_dict = dict()
        for k,v in crm_dict.items():
            try:
                if v.endswith('_parse'):
                    key = v.split('_parse')
                    value = get_field(record, k, key[0])
                    record_dict[key[0]] = value
                else:
                    record_dict[v] = record.get(k)
            except Exception:
                continue
        record_list.append(record_dict)
    return record_list

def sync_cultivars(record):
    """
    Webhook for Zoho CRM to sync cultivars real time.
    """
    crm_obj = get_crm_obj()
    record = json.loads(record.dict()['response'])
    record = parse_crm_record('Cultivars', [record])[0]
    try:
        obj, created = Cultivar.objects.update_or_create(
            cultivar_crm_id=record['cultivar_crm_id'],
            cultivar_name=record['cultivar_name'],
            defaults=record)
        return created
    except Exception as exc:
        print(exc)
        return {}

def fetch_cultivars(days=1):
    """
    Fetch cultivars from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S%z')
    request_headers = dict()
    request_headers['If-Modified-Since'] = date
    has_more = True
    page = 0
    while has_more != False:
        records = crm_obj.get_records(module='Cultivars', page=page, extra_headers=request_headers)['response']
        has_more = records['info']['more_records']
        page = records['info']['page'] + 1
        records = parse_crm_record('Cultivars', records['data'])
        for record in records:
            try:
                obj, created = Cultivar.objects.update_or_create(
                    cultivar_crm_id=record['cultivar_crm_id'], cultivar_name=record['cultivar_name'], defaults=record)
            except Exception as exc:
                print(exc)
                continue
    return

def get_labtest(id=None, sku=None):
    """
    Fetch labtest from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    if id:
        response = crm_obj.get_record('Testing', id)
    else:
        response = search_query('Testing', sku, 'Inventory_SKU')
    if response['status_code'] != 200:
        return response
    response = parse_crm_record('Testing', response['response'])
    return {'status_code': 200,
            'response': response}
    
def fetch_labtests(days=1):
    """
    Fetch labtests from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S%z')
    request_headers = dict()
    request_headers['If-Modified-Since'] = date
    has_more = True
    page = 0
    while has_more != False:
        records = crm_obj.get_records(module='Testing', page=page, extra_headers=request_headers)
        if records.get('response'):
            records = records['response']
            has_more = records['info']['more_records']
            page = records['info']['page'] + 1
            records = parse_crm_record('Testing', records['data'])
            for record in records:
                try:
                    obj, created = LabTest.objects.update_or_create(
                        labtest_crm_id=record['labtest_crm_id'], Inventory_SKU=record['Inventory_SKU'], defaults=record)
                except Exception as exc:
                    print(exc)
                    continue
    return

def sync_labtest(record):
    """
    Webhook for Zoho CRM to sync labtest real time.
    """
    crm_obj = get_crm_obj()
    record = json.loads(record.dict()['response'])
    record = parse_crm_record('Testing', [record])[0]
    try:
        obj, created = LabTest.objects.update_or_create(
            labtest_crm_id=record['labtest_crm_id'],
            Name=record['Name'],
            defaults=record)
        return created
    except Exception as exc:
        print(exc)
        return {}
