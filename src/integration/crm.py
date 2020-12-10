import ast
import json
from io import BytesIO
import hashlib
from datetime import (datetime, timedelta, )
from urllib.parse import (unquote, )
from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER,
    LICENSE_PARENT_FOLDER_ID,
    TEMP_LICENSE_FOLDER,
    AWS_BUCKET)
from django.conf import settings
from user.models import (User, )
from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from .crm_format import (CRM_FORMAT, VENDOR_TYPES,
                         ACCOUNT_TYPES)
from .box import (get_shared_link, move_file,
                  create_folder, upload_file_stream)
from core.celery import app
from .utils import (get_vendor_contacts, get_account_category,
                    get_cultivars_date, get_layout, get_overview_field,)
from core.mailer import mail, mail_send
from brand.models import (Brand, License, LicenseProfile, )
from integration.models import (Integration,)
from integration.apps.aws import (get_boto_client, )
from inventory.models import (Documents, )
from slacker import Slacker
slack = Slacker(settings.SLACK_TOKEN)

def get_crm_obj():
    """
    Return ZCRM object.
    """
    try:
        oauth = Integration.objects.get(name='crm')
        access_token = oauth.access_token
        access_expiry = oauth.access_expiry
    except Integration.DoesNotExist:
        access_expiry = access_token = None
    return CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER,
        access_token,
        access_expiry)

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

def parse_fields(module, key, value, obj, crm_obj, **kwargs):
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

    def get_employees(id):
        data = get_record('Contacts', id)
        if data.get('status_code') == 200:
            return data.get('response').get(id)
        return {}

    def get_contact_from_crm(obj, id, is_buyer=False, is_seller=False):
        if is_buyer:
            data = search_query('Accounts_X_Contacts', id, 'Accounts')
        elif is_seller:
            data = search_query('Vendors_X_Contacts', id, 'Vendor')
        return data.get('response')

    cultivator_starts_with = (
        "co.",
        "fo.",
        "cr.",
    )
    if value.startswith('ethics_and_certification'):
        if isinstance(obj.get(value), list) and len(obj.get(value)) > 0:
            return obj.get(value)
        return []
    if value.startswith('program_details'):
        d = obj.get('program_details')
        if d and len(d) > 0:
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
        return []
    list_fields = (
        'transportation',
        'cultivation_type',
        'vendor_type',
        'type_of_nutrients'
        )
    if value.startswith(list_fields):
        if isinstance(obj.get(value), list):
            return obj.get(value)
        return []
    boolean_conversion_list = ('issues_with_failed_labtest', 'cr.process_on_site', 'transportation')
    string_conversion_list = ('featured_on_our_site',)
    if value.startswith(boolean_conversion_list):
        return 'Yes' if obj.get(value) in [True, 'true', 'True'] else 'No'
    elif value.startswith(string_conversion_list):
        return True if obj.get(value) in ['true', 'True'] else False
    elif value.startswith(cultivator_starts_with):
        return get_overview_field(key, value, obj, crm_obj)
    if value in ('full_season', 'autoflower'):
        return "yes" if obj.get(value) else "No"
    if value.startswith(('billing_address', 'mailing_address')):
        v = value.split('.')
        if len(v) == 2 and obj.get(v[0]):
            return obj.get(v[0]).get(v[1])
    if value.startswith('cultivars'):
        cultivars = list()
        dictionary = obj.get('cr.overview')
        if dictionary:
            for i in dictionary:
                for j in i['cultivars']:
                    cultivars.extend(j['cultivar_names'])
        return list(set(cultivars))
    if value.startswith('contact_from_crm'):
        result = list()
        vendor_id = kwargs.get('vendor_id')
        account_id = kwargs.get('account_id')
        if vendor_id:
            data = get_contact_from_crm(obj, vendor_id, is_seller=True)
        elif account_id:
            data = get_contact_from_crm(obj, account_id, is_buyer=True)
        if data:
            for i in data:
                if vendor_id:
                    contact = get_employees(i['Contact']['id'])
                elif account_id:
                    contact = get_employees(i['Contacts']['id'])
                contact.update(i)
                result.append(contact)
            return result
        return []
    if value.startswith('Created_By'):
        return value
    
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
            else:
                v = record.get(v)
            if v and ((v is not None) or len(v)>0):
                record_dict[k] = v
        request.append(record_dict)
    response = crm_obj.update_records(module, request, is_return_orginal_data)
    return response

def delete_record(module, record_id):
    """
    Delete record from module.
    """
    crm_obj = get_crm_obj()
    response = crm_obj.delete_record(module, record_id)
    return response

def disassociate_brand(brand_name, vendor_name):
    """
    Disassociate brand from license.
    """
    response = search_query('Brands_X_Vendors', vendor_name, 'Vendor')
    if response.get('status_code') != 200:
        response = search_query('Brands_X_Accounts', vendor_name, 'Account')
    if response.get('status_code') == 200:
        for record in response.get('response'):
            if (record.get('Vendor') and record.get('Vendor').get('name') == vendor_name and
                record.get('Brand').get('name') == brand_name):
                return delete_record('Brands_X_Vendors', record.get('id'))
            elif (record.get('Account') and record.get('Account').get('name') == vendor_name and
                record.get('Brand').get('name') == brand_name):
                return delete_record('Brands_X_Accounts', record.get('id'))
    return response

def get_program_selection(program):
    """
    Return program selection.
    """
    PROGRAM_SELECTION = {
        'spot': 'Spot Market',
        'silver': 'IFP - Silver - Right of First Refusal',
        'gold': 'IFP - Gold - Exclusivity'
    }
    if "spot" in program:
        return PROGRAM_SELECTION['spot']
    elif "silver" in program:
        return PROGRAM_SELECTION['silver']
    elif "gold" in program:
        return PROGRAM_SELECTION['gold']
    else:
        return None

def update_vendor_tier(module, record):
    if record.get('program_selection'):
        crm_obj = get_crm_obj()
        request = dict()
        request['id'] = record.get('id')
        request['Program_Selection'] = get_program_selection(record.get('program_selection').lower())
        layout_name = record.get('Layout_Name')
        request['Layout'] = get_layout(module, layout_name)
        response = crm_obj.update_records(module, [request])
        return response
    return {'code': 1, 'status': 'Program selection not specified.'}

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
    final_list = dict()
    for i in licenses:
        try:
            final_dict = dict()
            d = dict()
            l = list()
            d.update(i)
            license_db_id= i['id']
            d.update({'license_db_id': license_db_id})
            license_db = License.objects.select_related().get(id=license_db_id)
            licenses = get_licenses(i['legal_business_name'])
            d.update(license_db.license_profile.__dict__)
            try:
                d.update(license_db.profile_contact.profile_contact_details)
            except Exception:
                pass
            vendor_id = license_db.license_profile.__dict__['id']
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
            try:
                d.update(license_db.program_overview.__dict__)
            except Exception:
                pass
            d.update({'license_id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
            l.append(d['license_id'])
            d.update({'licenses': l})
            if record and is_update:
                d['id'] = record.zoho_crm_id
            elif id and is_single_user and is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
            farm_name = license_db.license_profile.__dict__['name']
            response = update_license(farm_name, d)
            final_dict['license'] = response
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
            final_dict['vendor'] = result
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
                if result['response']['orignal_data'][0].get('Cultivars_List'):
                    data = dict()
                    l = list()
                    data['Cultivar_Associations'] = record_response[0]['details']['id']
                    for j in result['response']['orignal_data'][0]['Cultivars_List']:
                            r = search_query('Cultivars', j, 'Name')
                            if r['status_code'] == 200:
                                data['Cultivars'] = r['response'][0]['id']
                                r = create_records('Vendors_X_Cultivars', [data])
                request = list()
                contact_dict = {
                    'Owner1': 'Owner',
                    'Contact_1': 'Cultivation Manager',
                    'Contact_2': 'Logistics Manager',
                    'Contact_3': 'Sales Manager'}
                for contact in ['Owner1', 'Contact_1', 'Contact_2', 'Contact_3']:
                    data = dict()
                    user_id = result['response']['orignal_data'][0].get(contact)
                    if user_id:
                        if len(request) == 0:
                            data['Contact'] = user_id
                            data['Contact_Company_Role'] = [contact_dict[contact]]
                            data['Vendor'] = record_response[0]['details']['id']
                            request.append(data)
                        else:
                            inserted = False
                            for j in request:
                                if j.get('Contact') == user_id:
                                    j['Contact_Company_Role'].append(contact_dict[contact])
                                    inserted = True
                            if not inserted:
                                data['Contact'] = user_id
                                data['Contact_Company_Role'] = [contact_dict[contact]]
                                data['Vendor'] = record_response[0]['details']['id']
                                request.append(data)
                if is_update:
                    contact_response = update_records('Vendors_X_Contacts', request)
                else:
                    contact_response = create_records('Vendors_X_Contacts', request)
        except Exception as exc:
            print(exc)
            final_dict['exception'] = exc
        final_list[license_db_id] = final_dict
    return final_list
            
@app.task(queue="general")
def insert_vendors(id=None, is_update=False, is_single_user=False):
    """
    Insert Vendors into Zoho CRM.
    """
    if is_single_user:
        return insert_record(id=id, is_update=is_update, is_single_user=is_single_user)
    else:
        final_list = dict()
        if id:
            records = Brand.objects.filter(id=id)
        else:
            records = Brand.objects.filter(is_updated_in_crm=False)
        for record in records:
            final_dict = dict()
            if is_update:
                record.id = record.zoho_crm_id
                result = update_records('Brands', record.__dict__, True)
            else:
                result = create_records('Brands', record.__dict__, True)
            final_dict['brand'] = result['response']
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
            final_dict.update(record_response)
            for k,response in record_response.items():
                if (result['status_code'] == 201 and \
                    response['license']['status_code'] == 200 and \
                    response['vendor']['status_code'] == 201):
                    data = dict()
                    resp_brand = result['response']['response']['data']
                    resp_vendor = response['vendor']['response']['response']['data']
                    data['brands'] = resp_brand[0]['details']['id']
                    data['vendors'] = resp_vendor[0]['details']['id']
                    if is_update:
                        r = update_records('Brands_X_Vendors', [data])
                    else:
                        r = create_records('Brands_X_Vendors', [data])
            final_list[record.id] = final_dict
        return final_list

def upload_file_s3_to_box(aws_bucket, aws_key):
    """
    Upload file from s3 to box.
    """
    aws_client = get_boto_client('s3')
    file_obj = aws_client.get_object(Bucket=aws_bucket, Key=aws_key)
    md5sum = aws_client.head_object(Bucket=aws_bucket,Key=aws_key)['ETag'][1:-1]
    if file_obj.get('Body'):
       data = file_obj['Body'].read()
       aws_md5 = hashlib.md5(data).hexdigest()
       aws_sha1 = hashlib.sha1(data).hexdigest()
       data = BytesIO(data)
       box_file_obj = upload_file_stream(TEMP_LICENSE_FOLDER, data, aws_key.split('/')[-1])
       if isinstance(box_file_obj, str):
           return box_file_obj
       if (md5sum == aws_md5) and (box_file_obj.sha1 == aws_sha1):
           aws_client.delete_object(Bucket=aws_bucket, Key=aws_key)
       else:
           print('Checksum didnot match.', aws_bucket, aws_key)
       return box_file_obj
    return None

def update_license(dba, license):
    """
    Update license with shareable link.
    """
    response = None
    data = list()
    license_number = license['license_number']
    dir_name = f'{dba}_{license_number}'
    new_folder = create_folder(LICENSE_PARENT_FOLDER_ID, dir_name)
    license_folder = create_folder(new_folder, 'Licenses')
    if not license.get('uploaded_license_to'):
        try:
            license_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='license').first()
            license_to_path = license_to.path
            aws_bucket = AWS_BUCKET
            file_id = upload_file_s3_to_box(aws_bucket, license_to_path)
            moved_file = move_file(file_id, license_folder)
            license_url = get_shared_link(file_id)
            if license_url:
                license['uploaded_license_to'] = license_url  + "?id=" + moved_file.id
        except Exception as exc:
            print('Error in update license', exc)
            pass
    documents = create_folder(new_folder, 'documents')
    if not license.get('uploaded_sellers_permit_to'):
        try:
            seller_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='seller_permit').first()
            seller_to_path = seller_to.path
            aws_bucket = AWS_BUCKET
            file_id = upload_file_s3_to_box(aws_bucket, seller_to_path)
            moved_file = move_file(file_id, documents)
            license_url = get_shared_link(file_id)
            license['uploaded_sellers_permit_to'] = license_url  + "?id=" + moved_file.id
        except Exception as exc:
            print('Error in update license', exc)
            pass
    license_obj = License.objects.filter(pk=license['license_db_id']).update(
        uploaded_license_to=license.get('uploaded_license_to'),
        uploaded_sellers_permit_to=license.get('uploaded_sellers_permit_to')
    )
    data.append(license)
    response = update_records('Licenses', data)
    return response

def get_vendors_from_licenses(field, licenses):
    """
    Get vendor id from licenses.
    """
    vendor_lookup = licenses.get(field)
    if vendor_lookup:
        return vendor_lookup.get('id')

@app.task(queue="general")
def get_records_from_crm(license_number):
    """
    Get records from Zoho CRM using license number.
    """
    final_response = dict()
    licenses = search_query('Licenses', license_number, 'Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        for license_dict in licenses.get('response'):
            license_number = license_dict['Name']
            org = search_query('Orgs_X_Licenses', license_number, 'License')
            if org.get('status_code') == 200:
                org_list = list()
                for o in org.get('response'):
                    r = dict()
                    r['Org'] = o['Org']['name']
                    org_list.append(r)
                final_response['organization'] = org_list
            else:
                final_response['organization'] = None
            vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
            if vendor['status_code'] != 200:
                vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', license_dict)
            else:
                vendor = vendor['response'][0]['Licenses_Module']
                vendor_id = vendor['id']
            if not vendor_id:
                account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                if account['status_code'] != 200:
                    account_id = get_vendors_from_licenses('Account_Name_Lookup', license_dict)
                else:
                    account = account['response'][0]['Licenses_Module']
                    account_id = account['id']
                if not account_id:
                    final_response[license_number] = {'error': 'No association found for legal business name'}
                    continue
            crm_obj = get_crm_obj()
            if vendor_id:
                record = crm_obj.get_record('Vendors', vendor_id)
            elif account_id:
                record = crm_obj.get_record('Accounts', account_id)
            if record['status_code'] == 200:
                if vendor_id:
                    vendor = record['response'][vendor_id]
                elif account_id:
                    vendor = record['response'][account_id]
                # licenses = [licenses['response'][0]]
                licenses = license_dict
                if vendor.get('Licenses'):
                    license_list = vendor.get('Licenses').split(',')
                    license_list.remove(license_number)
                    for l in license_list:
                        license = search_query('Licenses', l.strip(), 'Name')
                        if license['status_code'] == 200:
                            license_dict.append(license['response'][0])
                crm_dict = get_format_dict('Licenses_To_DB')
                r = dict()
                for k, v in crm_dict.items():
                    r[k] = licenses.get(v)
                response = dict()
                if vendor_id:
                    crm_dict = get_format_dict('Vendors_To_DB')
                    response['vendor_type'] = get_vendor_types(vendor['Vendor_Type'], True)
                elif account_id:
                    crm_dict = get_format_dict('Accounts_To_DB')
                    response['vendor_type'] = get_vendor_types(vendor['Company_Type'], True)
                response['license'] = r
                record_dict = dict()
                for k,v in crm_dict.items():
                    if v.endswith('_parse'):
                        value = v.split('_parse')[0]
                        if vendor_id:
                            value = parse_fields('Vendors', k, value, vendor, crm_obj, vendor_id=vendor_id)
                        elif account_id:
                            value = parse_fields('Vendors', k, value, vendor, crm_obj, account_id=account_id)
                        record_dict[k] = value
                    else:
                        record_dict[k] = vendor.get(v)
                response['license_profile'] = record_dict
                if vendor_id:
                    response['is_seller'] = True
                    response['is_buyer'] = False
                elif account_id:
                    response['is_seller'] = False
                    response['is_buyer'] = True
                final_response[license_number] = response
        return final_response
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
    final_list = dict()
    for i in licenses:
        final_dict = dict()
        l = list()
        d = dict()
        d.update(i)
        license_db_id= i['id']
        d.update({'license_db_id': license_db_id})
        license_db = License.objects.select_related().get(id=license_db_id)
        licenses = get_licenses(i['legal_business_name'])
        d.update(license_db.license_profile.__dict__)
        try:
            d.update(license_db.profile_contact.profile_contact_details)
        except Exception:
                pass
        vendor_id = license_db.license_profile.__dict__['id']
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
        d.update({'license_id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
        l.append(d['license_id'])
        d.update({'licenses': l})    
        if record and is_update:
            d['id'] = record.zoho_crm_id
        elif id and is_single_user and is_update:
            d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
        farm_name = license_db.license_profile.__dict__['name']
        response = update_license(farm_name, d)
        final_dict['license'] = response
        if response['status_code'] == 200:
            record_response = response['response']['data']
            try:
                record_obj = License.objects.get(id=license_db_id)
                record_obj.zoho_crm_id = record_response[0]['details']['id']
                record_obj.is_updated_in_crm = True
                record_obj.save()
            except KeyError as exc:
                print(exc)
        if is_update:
            result = update_records('Accounts', d, is_return_orginal_data=True)
        else:    
            result = create_records('Accounts', d, is_return_orginal_data=True)
        final_dict['account'] = result
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
                    if is_update:
                        r = update_records('Accounts_X_Licenses', [data])
                    else:
                        r = create_records('Accounts_X_Licenses', [data])
                request = list()
                contact_dict = {
                    'Owner1': 'Owner',
                    'Contact_1': 'Cultivation Manager',
                    'Contact_2': 'Logistics Manager',
                    'Contact_3': 'Sales Manager'}
                for contact in ['Owner1', 'Contact_1', 'Contact_2', 'Contact_3']:
                    data = dict()
                    user_id = result['response']['orignal_data'][0].get(contact)
                    if user_id:
                        if len(request) == 0:
                            data['Contacts'] = user_id
                            data['Contact_Company_Role'] = [contact_dict[contact]]
                            data['Accounts'] = record_response[0]['details']['id']
                            request.append(data)
                        else:
                            inserted = False
                            for j in request:
                                if j.get('Contacts') == user_id:
                                    j['Contact_Company_Role'].append(contact_dict[contact])
                                    inserted = True
                            if not inserted:
                                data['Contacts'] = user_id
                                data['Contact_Company_Role'] = [contact_dict[contact]]
                                data['Accounts'] = record_response[0]['details']['id']
                                request.append(data)
                if is_update:
                    contact_response = update_records('Accounts_X_Contacts', request)
                else:
                    contact_response = create_records('Accounts_X_Contacts', request)
        final_list[license_db_id] = final_dict
    return final_list

@app.task(queue="general")
def insert_accounts(id=None, is_update=False, is_single_user=False):
    """
    Insert new accounts in Zoho CRM.
    """
    if is_single_user:
        return insert_account_record(id=id, is_single_user=is_single_user)
    else:
        final_list = dict()
        if id:
            records = Brand.objects.filter(id=id).select_related()
        else:
            records = Brand.objects.filter(is_updated_in_crm=False).select_related()
        for record in records:
            final_dict = dict()
            try:
                if is_update:
                    result = update_records('Brands', record.__dict__, True)
                else:
                    result = create_records('Brands', record.__dict__, True)
                final_dict['brand'] = result
                if result['status_code'] == 201:
                    try:
                        record_obj = Brand.objects.get(id=id)
                        record_obj.zoho_crm_id = result['response']['response']['data'][0]['details']['id']
                        record_obj.is_updated_in_crm = True
                        record_obj.save()
                    except KeyError as exc:
                        print(exc)
                        continue
                record_response = insert_account_record(record=record, is_update=is_update)
                final_dict.update(record_response)
                for k, response in record_response.items():
                    if (result['status_code'] == 201 and \
                        response['license']['status_code'] == 200 and \
                        response['account']['status_code'] == 201):
                        data = dict()
                        resp_brand = result['response']['response']['data']
                        resp_account = response['account']['response']['response']['data']
                        data['brands'] = resp_brand[0]['details']['id']
                        data['accounts'] = resp_account[0]['details']['id']
                        if is_update:
                            r = update_records('Brands_X_Accounts', [data])
                        else:
                            r = create_records('Brands_X_Accounts', [data])
            except Exception as exc:
                print(exc)
                final_dict['exception'] = exc
                continue
            final_list[record.id] = final_dict
        return final_list

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
                if v.endswith('_parse'):
                    value = v.split('_parse')[0]
                    value = parse_fields('Accounts', k, value, account, crm_obj, account_id=account_id)
                    response[k] = value
                else:
                    response[k] = account.get(v)
            return response
    return {}


def post_leads_to_slack_and_email(record,response):
    """
    Post New leads on slack.
    """
    try:
        lead_crm_link = settings.ZOHO_CRM_URL+"/crm/org"+settings.CRM_ORGANIZATION_ID+"/tab/Leads/"+response.get('response')['data'][0]['details']['id']+"/"
        msg = """New lead is added via connect page with the details as:\n- First Name:%s\n- Last Name:%s\n- Company Name:%s\n -Title:%s\n- Vendor Category:%s\n- Heard From:%s\n- Phone:%s\n- Message:%s\n- Email:%s\n- Lead Origin:%s\n- Lead CRM Link:<%s> """ %(record.get("first_name"),record.get("last_name"),record.get("company_name"),record.get("title"),','.join(record.get("vendor_category")),record.get("heard_from"),record.get("phone"),record.get("message"),record.get("email"),record.get("Lead_Origin"),lead_crm_link)
        slack.chat.post_message(settings.SLACK_SALES_CHANNEL,msg, as_user=True)
        mail_send("connect.html",{'first_name': record.get("first_name"),'last_name':record.get("last_name"),'mail':record.get("email"),'company_name':record.get("company_name"),'title':record.get("title"),'vendor_category':','.join(record.get("vendor_category")),'heard_from':record.get("heard_from"),'phone':record.get("phone"),'message':record.get("message"),'lead_origin':record.get("Lead_Origin"),'lead_crm_link':lead_crm_link},"New lead via connect page.",'connect@thrive-society.com')
    except Exception as e:
        print("Exception while posting to slack & email on lead creation.")
    

@app.task(queue="general")
def create_lead(record):
    """
    Create lead in Zoho CRM.
    """
    record.update({"Lead_Origin":"Connect Form"})
    response = create_records('Leads', record)
    post_leads_to_slack_and_email(record,response)
    return response

def get_field(record, key, field):
    """
    Parse crm fields.
    """
    date_fields = [
        # 'Date_Harvested',
        'Date_Received',
        'Date_Reported',
        'Date_Tested',
        # 'Created_Time',
        'Last_Activity_Time',
        # 'Modified_Time',
    ]
    labtest_float_values = ['THC', 'CBD', 'THCA',
                            'THCVA', 'THCV', 'CBDA',
                            'CBGA', 'CBG', 'CBN',
                            'CBL', 'CBCA', 'CBC', 'CBDV',
                            'Cannabinoids', 'Total_CBD', 'CBDVA',
                            'Total_Cannabinoids', 'Total_THC',
                            'd_8_THC', 'Total_CBD']
    if field in labtest_float_values:
        v = record.get(field)
        if '%' in v:
            v = v.strip('%')
        if v == 'NA':
            v = "-1"
        elif v == 'ND':
            v = "-2"
        elif v == 'NT':
            v = "-3"
        return float(v)
    if field in ('Created_By', 'Modified_By'):
        return record.get(key)
    if field in ('parent_1', 'parent_2'):
        return [record.get(key).get('id')]
    if field in ('Created_Time', 'Date_Harvested', 'Modified_Time'):
        return datetime.strptime(record.get(key), '%Y-%m-%dT%H:%M:%S%z').date()
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
            except Exception as exc:
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
        response = crm_obj.get_full_record('Testing', id)
    else:
        response = search_query('Testing', sku, 'Inventory_SKU')
    if response['status_code'] != 200:
        return response
    if id:
        response = parse_crm_record('Testing', [response['response']])
    elif sku:
        response = parse_crm_record('Testing', [response['response'][id]])
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

def fetch_licenses():
    """
    Fetch licenses and update in database.
    """
    success_count = 0
    error_count = 0
    error_licenses = list()
    success_licenses = list()
    licenses = License.objects.all()
    for license in licenses:
        crm_license = search_query('Licenses', license.license_number, 'Name')
        crm_license = crm_license.get('response')
        if crm_license and len(crm_license) > 0:
            for l in crm_license:
                try:
                    if l['Name'] == license.license_number and l['id'] == license.zoho_crm_id:
                        if license.expiration_date != l['Expiration_Date'] and \
                            license.issue_date != l['Issue_Date']:
                            license.expiration_date = l['Expiration_Date']
                            license.issue_date = l['Issue_Date']
                            license.is_updated_via_trigger = True
                            license.save()
                            success_count += 1
                            success_licenses.append(license.license_number)
                except Exception as exc:
                    print(exc)
                    continue
        else:
            print('license not found in database -', license.license_number)
            error_count += 1
            error_licenses.append(license.license_number)
    return {'success_count': success_count, 'error_count': error_count}