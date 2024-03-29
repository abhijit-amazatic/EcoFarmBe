import sys
import traceback
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
from django.core.exceptions import (ObjectDoesNotExist,)
from user.models import (User, )
from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from .crm_format import (CRM_FORMAT, VENDOR_TYPES,
                         VENDOR_LICENSE_TYPES, ACCOUNT_LICENSE_TYPES,
                         ACCOUNT_TYPES, LICENSE_TYPE_TO_VENDOR_TYPE)
from integration.box import (get_shared_link, move_file,
                  create_folder, upload_file_stream, get_folder_obj)
from core.celery import app
from integration.utils import (get_vendor_contacts, get_account_category,
                    get_cultivars_date, get_layout, get_overview_field,)
from core.mailer import mail, mail_send
from brand.models import (Brand, License, LicenseProfile, Organization, ProgramOverview, NurseryOverview)
from integration.models import (Integration,)
from integration.apps.aws import (get_boto_client, )
from inventory.models import (Documents, Inventory)
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
            if field['api_name'] == field_name and field['data_type'] in picklist_types:
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

# def get_dict(cd, i):
# def get_dict(cd, i):
#     d = dict()
#     for k, v in cd.items():
#         d[k] = i.get(v)
#     return d

def get_users(user_type='ActiveUsers', email=None, page=1, per_page=200):
    """
    Get users from zoho CRM.
    """
    crm_obj = get_crm_obj()
    response = crm_obj.get_users(user_type, page=page, per_page=per_page)
    if response.get('status_code') != 200:
        return response
    if email:
        for i in response.get('response'):
            if i['email'] == email:
                return i
        return []
    return response

def get_user(user_id):
    """
    Get user from zoho CRM.
    """
    crm_obj = get_crm_obj()
    return crm_obj.get_user(user_id)

# def create_employees(key, value, obj, crm_obj):
#     """
#     Create contacts in Zoho CRM.
#     """
#     d = obj.get(value)
#     cd = {
#         'last_name': 'employee_name',
#         'email': 'employee_email',
#         'phone': 'phone',
#     }
#     if key == 'Contacts_List':
#         contacts = list()
#         try:
#             for i in d:
#                 user = get_dict(cd, i)
#                 user = get_dict(cd, i)
#                 if user.get('email'):
#                     r = create_records('Contacts', [user])
#                     if r['status_code'] in (201, 202):
#                         try:
#                             contact_id = r['response']['data'][0]['details']['id']
#                         except Exception:
#                             pass
#                         else:
#                             contacts.append({
#                                 'roles': i.get('roles', []),
#                                 'contact_crm_id': contact_id,
#                             })


#             return contacts
#         except IndexError:
#             return []
#         except TypeError:
#             return []

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
    # if not obj.get(value):
        # return None
    if value.startswith('county') or value.startswith('appellation'):
        if obj.get(value):
            return obj.get(value).split(',')
        return []
    if value.startswith('County2') or value.startswith('Appellations'):
        if isinstance(obj.get(value), list):
            return ','.join(obj.get(value))
    if value.startswith('ethics_and_certification'):
        if isinstance(obj.get(value), list) and len(obj.get(value)) > 0:
            return obj.get(value)
        return []
    if value.startswith('program_details'):
        d = obj.get('program_details')
        if d and len(d) > 0:
            return d.get('program_name')
    # if value.startswith('employees'):
    #     return create_employees(key, value, obj, crm_obj)
    if value == 'brand_category':
        return get_vendor_types(obj.get(value))
    if value == 'Vendor_Type':
        if obj.get('license_type'):
            return LICENSE_TYPE_TO_VENDOR_TYPE.get(obj.get('license_type'), [])
        return []
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
    if value.startswith('cultivation_type_list'):
        v = obj.get('cultivation_type')
        if isinstance(v, str):
            return [v]
        return []

    list_fields = (
        'transportation',
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
    if value.startswith('verified'):
        return "Yes" if obj.get('status') == 'approved' else "No"
    if value.startswith(('billing_address', 'mailing_address')):
        v = value.split('.')
        if len(v) == 2 and obj.get(v[0]):
            return obj.get(v[0]).get(v[1])
    if value.startswith('Farm_Contact_first_Name'):
        user_id = obj.get('created_by_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except Exception:
                pass
            else:
                return user.first_name
        return ''
    if value.startswith('Farm_Contact_Last_Name'):
        user_id = obj.get('created_by_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except Exception:
                pass
            else:
                return user.last_name
        return ''
    if value.startswith('Cultivars'):
        if obj.get(value):
            return obj.get(value).split(', ')
        return []
    # if value.startswith('cultivars_of_interest'):
    #     if isinstance(obj.get(value), list):
    #         cult_ls = []
    #         for cultivar in obj.get(value):
    #             try:
    #                 r = search_query('Cultivars', cultivar, 'Name')
    #                 if r['status_code'] == 200:
    #                     cult_ls.append(r['response'][0]['id'])
    #             except Exception as e:
    #                 print(e)
    #         return cult_ls
    #     return obj.get(value)
    if value.startswith('cultivars'):
        cultivars = list()
        try:
            crop_overview = obj.get('cr.overview')
            if crop_overview and isinstance(crop_overview, dict):
                for j in crop_overview.get('cultivars'):
                    cultivars.extend(j['cultivar_names'])
        except Exception as e:
            print(e)
        return list(set(cultivars))
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

def update_in_crm(module, record_id):
    """
    Update record in zoho crm.
    """
    request = dict()
    try:
        if module in ['Vendors', 'Accounts']:
            lp_obj = LicenseProfile.objects.select_related('license').get(id=record_id)
            request = lp_obj.license.__dict__
            request.update(lp_obj.__dict__)
            if module == 'Accounts':
                request['id'] = request.get('zoho_crm_account_id')
            else:
                request['id'] = request.get('zoho_crm_vendor_id')
                if lp_obj.license.profile_category == 'nursery':
                    request['Layout_Name'] = 'vendor_cannabis_nursery'
                # elif lp_obj.license.profile_category in ('distribution', 'manufacturing', 'retail', 'microbusiness',):
                #     request['Layout_Name'] = 'vendor_cannabis_non_cultivator'
                else:
                    request['Layout_Name'] = 'vendor_cannabis'
        else:
            if module == 'Licenses':
                license_obj = License.objects.select_related('license_profile').get(id=record_id)
                try:
                    request.update(license_obj.license_profile.__dict__)
                except ObjectDoesNotExist:
                    pass
                request.update(license_obj.__dict__)
            elif module == 'Orgs':
                request = Organization.objects.get(id=record_id)
                request = request.__dict__
            elif module == 'Brands':
                request = Brand.objects.get(id=record_id)
                request = request.__dict__

            if request:
                request['id'] = request.get('zoho_crm_id')

    except Exception as exc:
        print(exc)
        return {'error': 'Record not in database'}
    if request.get('id'):
        return update_records(module, request)
    return {'error': 'Record not in CRM'}

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

def search_query(module, query, criteria, case_insensitive=False, is_license=False):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
    if case_insensitive:
        return crm_obj.isearch_record(module, query, criteria)
    if is_license:
        return crm_obj.search_license(module, query, criteria)
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


def get_licenses(license_field, license_number):
    """
    Get license from Zoho CRM.
    """
    licenses = search_query('Licenses', license_field, 'Legal_Business_Name')
    if licenses['status_code'] == 200:
        for license in licenses['response']:
            if license.get('Name') == license_number:
                return license

def is_user_existing(license_number):
    """
    Check if user is existing or not.
    """
    licenses = search_query('Licenses', license_number, 'Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        for license_dict in licenses.get('response'):
            vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
            if vendor['status_code'] != 200:
                vendor_id = get_lookup_id(license_dict, 'Vendor_Name_Lookup',)
            else:
                vendor = vendor['response'][0]['Licenses_Module']
                vendor_id = vendor['id']
            if not vendor_id:
                account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                if account['status_code'] != 200:
                    account_id = get_lookup_id(license_dict, 'Account_Name_Lookup')
                else:
                    account = account['response'][0]['Licenses_Module']
                    account_id = account['id']
                if not account_id:
                    return False, None
                else:
                    return True, 'Buyer'
            else:
                return True, 'Seller'
    return None

def upload_file_s3_to_box(aws_bucket, aws_key):
    """
    Upload file from s3 to box.
    """
    aws_client = get_boto_client('s3')
    print(aws_bucket, aws_key)
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

def update_license(dba, license=None, license_id=None, is_return_orginal_data=False):
    """
    Update license with shareable link.
    """
    response = None
    data = list()
    if not license and license_id:
        license = dict()
        try:
            license_obj = License.objects.get(id=license_id)
            try:
                license.update(license_obj.license_profile.__dict__)
            except ObjectDoesNotExist:
                pass
        except License.DoesNotExist:
            return {'error': f'License {license_id} not in database'}
        license.update(license_obj.__dict__)
        license['license_db_id'] = license['id']
        license['id'] = license['zoho_crm_id']
    license_number = license['license_number']
    dir_name = f'{dba}_{license_number}'
    new_folder = create_folder(LICENSE_PARENT_FOLDER_ID, dir_name)
    try:
        folder_obj = get_folder_obj(new_folder)
        folder_link = folder_obj.get_shared_link()
    except Exception:
        pass
    else:
        if folder_link:
            License.objects.filter(pk=license['license_db_id']).update(
                box_folder_id=new_folder,
                box_folder_url=folder_link,
            )
            license['box_folder_id'] = new_folder
            license['box_folder_url'] = folder_link
    license_folder = create_folder(new_folder, 'Licenses')
    if not license.get('uploaded_license_to') or license_id:
        try:
            license_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='license').latest('created_on')
            license_to_path = license_to.path
            aws_bucket = AWS_BUCKET
            box_file = upload_file_s3_to_box(aws_bucket, license_to_path)
            if isinstance(box_file, str):
                file_id = box_file
            else:
                file_id = box_file.id
            moved_file = move_file(file_id, license_folder)
            license_url = get_shared_link(file_id)
            if license_url:
                license['uploaded_license_to'] = license_url + "?id=" + moved_file.id
                license_to.box_url = license_url
                license_to.box_id = moved_file.id
                license_to.save()
        except Exception as exc:
            print('Error in update license', exc)
            pass
    # documents = create_folder(new_folder, 'documents')
    if not license.get('uploaded_sellers_permit_to') or license_id:
        try:
            seller_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='seller_permit').latest('created_on')
            seller_to_path = seller_to.path
            aws_bucket = AWS_BUCKET
            box_file = upload_file_s3_to_box(aws_bucket, seller_to_path)
            if isinstance(box_file, str):
                file_id = box_file
            else:
                file_id = box_file.id
            moved_file = move_file(file_id, license_folder)
            seller_permit_url = get_shared_link(file_id)
            if seller_permit_url:
                license['uploaded_sellers_permit_to'] = seller_permit_url + "?id=" + moved_file.id
                seller_to.box_url = seller_permit_url
                seller_to.box_id = moved_file.id
                seller_to.save()
        except Exception as exc:
            print('Error in update license', exc)
            pass
    if not license.get('uploaded_w9_to') or license_id:
        try:
            w9_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='w9').latest('created_on')
            w9_to_path = w9_to.path
            aws_bucket = AWS_BUCKET
            box_file = upload_file_s3_to_box(aws_bucket, w9_to_path)
            if isinstance(box_file, str):
                file_id = box_file
            else:
                file_id = box_file.id
            moved_file = move_file(file_id, license_folder)
            w9_url = get_shared_link(file_id)
            if w9_url:
                license['uploaded_w9_to'] = w9_url + "?id=" + moved_file.id
                license_to.box_url = w9_url
                license_to.box_id = moved_file.id
                license_to.save()
        except Exception as exc:
            print('Error in update license', exc)
            pass
    license_obj = License.objects.filter(pk=license['license_db_id']).update(
        uploaded_license_to=license.get('uploaded_license_to'),
        uploaded_sellers_permit_to=license.get('uploaded_sellers_permit_to'),
        uploaded_w9_to=license.get('uploaded_w9_to'),
        is_notified_before_expiry=False
    )
    data.append(license)
    response = update_records('Licenses', data, is_return_orginal_data)
    return response

def get_lookup_id(data_dict, field):
    """
    Get id from lookup field in data_dict.
    """
    lookup_info = data_dict.get(field)
    if lookup_info:
        return lookup_info.get('id')


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



def post_leads_to_slack_and_email(record,lead_id):
    """
    Post New leads on slack.
    """
    try:
        lead_crm_link = f"{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Leads/{lead_id}/"
        msg = (
            "New lead is added via connect page with the details as:\n"
            "- First Name: {first_name}\n"
            "- Last Name: {last_name}\n"
            "- Company Name: {company_name}\n"
            "- Title: {title}\n"
            "- Company Type: {Company_Type}\n"
            "- Heard From: {heard_from}\n"
            "- Phone: {phone}\n"
            "- Message: {message}\n"
            "- Email: {email}\n"
            "- Lead Origin: {Lead_Origin}\n"
            "- Lead CRM Link: <{lead_crm_link}>"
        ).format(**record, lead_crm_link=lead_crm_link)
        slack.chat.post_message(
            settings.SLACK_SALES_CHANNEL,
            msg,
            as_user=False,
            username=settings.BOT_NAME,
            icon_url=settings.BOT_ICON_URL
        )
        if not record.get('Email_Opt_Out'):
            mail_send(
                "connect.html",
                {
                    **record,
                    'vendor_category':','.join(record.get("vendor_category")),
                    'lead_crm_link':lead_crm_link
                },
                "New lead via connect page.",
                'connect@thrive-society.com'
            )
    except Exception as e:
        print("Exception while posting to slack & email on lead creation.")
    

@app.task(queue="general")
def create_lead(record):
    """
    Create lead in Zoho CRM.
    """
    record.update({"Lead_Origin":"Connect Form"})
    if isinstance(record.get('Company_Type'), list):
        record['Company_Type'] = record.get('Company_Type')[0]
    subscribe_to_newsletters = record.pop('subscribe_to_newsletters')
    if subscribe_to_newsletters not in ('true', 'True', True):
        record.update({"Email_Opt_Out": True})
    response = create_records('Leads', record)
    if response.get('status_code') in (200, 201):
        lead_id = response.get('response')['data'][0]['details']['id']
        post_leads_to_slack_and_email(record, lead_id)
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
        return [record.get(key).get('name')]
    if field in ('Created_Time', 'Date_Harvested', 'Modified_Time'):
        return datetime.strptime(record.get(key), '%Y-%m-%dT%H:%M:%S%z').date()
    if field in date_fields:
        return datetime.strptime(record.get(key), '%Y-%m-%d')
    if field.startswith('Total_Terpenes'):
        if record.get(key):
            return record.get(key)
        return 0


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

def update_or_create_cultivar(record):
    qs = Cultivar.objects.filter(cultivar_crm_id=record['cultivar_crm_id'])
    if qs.exists():
        qs.update(**record)
        return False
    else:
        obj = Cultivar.objects.create(**record)
        return True

def sync_cultivars(record):
    """
    Webhook for Zoho CRM to sync cultivars real time.
    """
    crm_obj = get_crm_obj()
    record = json.loads(record.dict()['response'])
    record = parse_crm_record('Cultivars', [record])[0]
    record['status'] = 'approved'
    try:
        return update_or_create_cultivar(record)
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
            record['status'] = 'approved'
            try:
                created = update_or_create_cultivar(record)
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
        if obj.Sample_I_D:
            items = Inventory.objects.filter(cf_lab_test_sample_id=obj.Sample_I_D)
            if items.exists():
                items.update(labtest=obj)
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


def fetch_record_owners(license_number=None, update_all=False):
    """
    Fetch vendor/account owner for license_number or
    Fetch owner for all records which don't have owner in db.
    """
    vendor_id = None
    account_id = None
    final_response = dict()
    if license_number:
        records = License.objects.filter(license_number=license_number)
    elif update_all:
        records = License.objects.filter(license_profile__crm_owner_id__isnull=True)
    for record in records:
        full_record = dict()
        license_number = record.license_number
        licenses = search_query('Licenses', license_number, 'Name')
        if licenses['status_code'] == 200 and len(licenses['response']) > 0:
            for license_dict in licenses.get('response'):
                vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
                if vendor['status_code'] != 200:
                    vendor_id = get_lookup_id(license_dict, 'Vendor_Name_Lookup')
                else:
                    vendor = vendor['response'][0]['Licenses_Module']
                    vendor_id = vendor['id']
                if not vendor_id:
                    account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                    if account['status_code'] != 200:
                        account_id = get_lookup_id(license_dict, 'Account_Name_Lookup')
                    else:
                        account = account['response'][0]['Licenses_Module']
                        account_id = account['id']
                    if not account_id:
                        final_response[license_number] = {'error': 'No association found for legal business name'}
                        continue
        crm_obj = get_crm_obj()
        if vendor_id:
            full_record = crm_obj.get_full_record('Vendors', vendor_id)
        elif account_id:
            full_record = crm_obj.get_full_record('Accounts', account_id)
        else:
            continue
        if full_record.get('status_code') == 200:
            owner = full_record.get('response').get('Owner')
            try:
                license_profile = LicenseProfile.objects.get(id=record.license_profile.id)
            except LicenseProfile.DoesNotExist:
                final_response[license_number] = {'error': 'License does not exist in database.'}
                continue
            license_profile.crm_owner_id = owner.get('id')
            license_profile.crm_owner_email = owner.get('email')
            license_profile.save()
            final_response[license_number] = license_profile
    return final_response



def create_or_update_org_in_crm(org_obj):
    result = search_query('Orgs', org_obj.__dict__['name'], 'Name')
    if result.get('status_code') == 200:
        organization_id = result.get('response')[0].get('id')
        result = update_records('Orgs', org_obj.__dict__, True)
        if organization_id and org_obj.zoho_crm_id != organization_id:
            org_obj.zoho_crm_id = organization_id
            org_obj.save()
    else:
        try:
            result = create_records('Orgs', org_obj.__dict__)
        except Exception as exc:
                print('Error while creating Organization in Zoho CRM')
                print(exc)
        if result.get('status_code') in [200, 201]:
            try:
                organization_id = result['response'][0]['id']
            except KeyError:
                try:
                    organization_id = result['response']['data'][0]['details']['id']
                except KeyError:
                    organization_id = None
            if organization_id:
                org_obj.zoho_crm_id = organization_id
                org_obj.save()
            else:
                print('Error while Extrating zoho_crm_id for created Organization in Zoho CRM')
                print(result)
        else:
            print('Error while creating Organization in Zoho CRM')
            print(result)
