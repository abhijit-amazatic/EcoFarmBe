# from .core import *
from core.celery import app

from .core import (
    get_crm_obj,
    get_format_dict,
    parse_fields,
    search_query,
    get_lookup_id,
)


def get_associated_vendor_from_license(crm_license_dict):
    vendor_id = get_lookup_id(crm_license_dict, 'Vendor_Name_Lookup')
    if not vendor_id:
        license_number = crm_license_dict['Name']
        vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
        if vendor['status_code'] == 200:
            vendor = vendor['response'][0]['Licenses_Module']
            vendor_id = vendor['id']
    return vendor_id

def get_associated_account_from_license(crm_license_dict):
    account_id = get_lookup_id(crm_license_dict, 'Account_Name_Lookup')
    if not account_id:
        license_number = crm_license_dict['Name']
        account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
        if account['status_code'] == 200:
            account = account['response'][0]['Licenses_Module']
            account_id = account['id']
    return account_id

def get_crm_vendor_to_db(vendor_id):
    if vendor_id:
        crm_obj = get_crm_obj()
        record = crm_obj.get_full_record('Vendors', vendor_id)
        if record['status_code'] == 200:
            vendor = record['response']
            crm_dict = get_format_dict('Vendors_To_DB')
            # response['vendor_type'] = get_vendor_types(vendor['Vendor_Type'], True)
            record_dict = dict()
            for k, v in crm_dict.items():
                if v.endswith('_parse'):
                    value = v.split('_parse')[0]
                    value = parse_fields('Vendors', k, value, vendor, crm_obj, vendor_id=vendor_id)
                    record_dict[k] = value
                else:
                    record_dict[k] = vendor.get(v)
            record_dict['zoho_crm_vendor_id'] = vendor_id
            return record_dict
    return {}

def get_crm_account_to_db(account_id, id_flat=False):
    if account_id:
        crm_obj = get_crm_obj()
        record = crm_obj.get_full_record('Accounts', account_id)
        if record['status_code'] == 200:
            account = record['response']
            crm_dict = get_format_dict('Accounts_To_DB')
            # response['vendor_type'] = get_vendor_types(vendor['Company_Type'], True)
            record_dict = dict()
            for k, v in crm_dict.items():
                if v.endswith('_parse'):
                    value = v.split('_parse')[0]
                    value = parse_fields('Accounts', k, value, account, crm_obj, account_id=account_id)
                    record_dict[k] = value
                else:
                    record_dict[k] = account.get(v)
            record_dict['zoho_crm_account_id'] = account_id
            return record_dict
    return {}

def get_records_from_crm(license_number):
    """
    Get records from Zoho CRM using license number.
    """
    final_response = dict()
    licenses = search_query('Licenses', license_number, 'Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        for license_dict in licenses.get('response'):
            license_number = license_dict['Name']
            vendor_id = get_associated_vendor_from_license(license_dict)
            account_id = get_associated_account_from_license(license_dict)

            if vendor_id:
                org = search_query('Orgs_X_Vendors', vendor_id, 'Vendor')
            elif account_id:
                org = search_query('Orgs_X_Accounts', account_id, 'Account')
            else:
                org = dict()
            if org.get('status_code') == 200:
                org_list = list()
                for o in org.get('response'):
                    r = dict()
                    if o.get('Org'):
                        r['name'] = o['Org']['name']
                        r['id'] = o['Org']['id']
                        org_list.append(r)
                final_response['organization'] = org_list
            else:
                final_response['organization'] = org

            if vendor_id:
                brand = search_query('Brands_X_Vendors', vendor_id, 'Vendor')
            elif account_id:
                brand = search_query('Brands_X_Accounts', account_id, 'Account')
            else:
                brand = dict()
            if brand.get('status_code') == 200:
                try:
                    brand_list = list()
                    for b in brand.get('response'):
                        r = dict()
                        r['name'] = b['Brand']['name']
                        r['id'] = b['Brand']['id']
                        brand_list.append(r)
                    final_response['Brand'] = brand_list
                except TypeError:
                    pass
            else:
                final_response['Brand'] = brand

            crm_obj = get_crm_obj()

            # licenses = [licenses['response'][0]]
            licenses = license_dict
            # if vendor.get('Licenses'):
            #     license_list = vendor.get('Licenses').split(',')
            #     license_list.remove(license_number)
            #     for l in license_list:
            #         license = search_query('Licenses', l.strip(), 'Name')
            #         if license['status_code'] == 200:
            #             license_dict.append(license['response'][0])
            #         else:
            #             license_dict.append(license)
            crm_dict = get_format_dict('Licenses_To_DB')
            r = dict()
            for k, v in crm_dict.items():
                r[k] = licenses.get(v)
            response = dict()
            response['license'] = r

            response['vendor'] = get_crm_vendor_to_db(vendor_id)
            response['account'] = get_crm_account_to_db(account_id)
            final_response[license_number] = response
        return final_response
    return licenses



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
            account_id = get_lookup_id(licenses['response'][0], 'Account_Name_Lookup',)
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


def get_vendors_from_crm(legal_business_name):
    """
    Fetch existing vendors from Zoho CRM.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        license_number = licenses['response'][0]['Name']
        vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
        if vendor['status_code'] != 200:
            vendor_id = get_lookup_id(licenses['response'][0], 'Vendor_Name_Lookup')
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
            crm_dict = get_format_dict('Vendors_To_DB')
            response = dict()
            response['licenses'] = li
            for k,v in crm_dict.items():
                if v.endswith('_parse'):
                    value = v.split('_parse')[0]
                    value = parse_fields('Vendors', k, value, vendor, crm_obj, vendor_id=vendor_id)
                    response[k] = value
                else:
                    response[k] = vendor.get(v)
            return response
    return {}

def get_associations(module, search_field, search_id, related_field_name, include_fields=dict(), id_flat=False):
    final_response = []
    resp = search_query(module, search_id, search_field)
    if resp.get('status_code') == 200:
        for record in resp.get('response'):
            related_field = record[related_field_name] or {}
            if related_field:
                if id_flat:
                    final_response.append(related_field['id'])
                else:
                    data = {
                        'id' :  related_field['id'],
                        'name': related_field['name'],
                        'linking_obj_id': record['id']
                    }
                    if include_fields:
                        for k, v in include_fields.items():
                            data[k] = record.get(v)
                    final_response.append(data)
    return final_response

def get_vendor_associated_organizations(vendor_id, id_flat=False):
    return get_associations('Orgs_X_Vendors', 'Vendor', vendor_id, 'Org', id_flat=id_flat)

def get_vendor_associated_brands(vendor_id, id_flat=False):
    return get_associations('Brands_X_Vendors', 'Vendor', vendor_id, 'Brand', id_flat=id_flat)

def get_vendor_associated_licenses(vendor_id, id_flat=False):
    return get_associations('Vendors_X_Licenses', 'Vendor', vendor_id, 'Licenses', id_flat=id_flat)

def get_vendor_associated_contacts(vendor_id, id_flat=False):
    return get_associations('Vendors_X_Contacts', 'Vendor', vendor_id, 'Contact', include_fields={'roles': 'Contact_Company_Role'}, id_flat=id_flat)

def get_vendor_associated_cultivars(vendor_id, id_flat=False):
    return get_associations('Vendors_X_Cultivars', 'Cultivar_Associations', vendor_id, 'Cultivars', id_flat=id_flat)

def get_vendor_associations(vendor_id, organizations=True, brands=True, licenses=True, contacts=True, cultivars=True):
    final_response = {}
    if organizations:
        final_response['Orgs'] = get_vendor_associated_organizations(vendor_id)
    if brands:
        final_response['Brands'] = get_vendor_associated_brands(vendor_id)
    if licenses:
        final_response['Licenses'] = get_vendor_associated_licenses(vendor_id)
    if contacts:
        final_response['Contacts'] = get_vendor_associated_contacts(vendor_id)
    if cultivars:
        final_response['Cultivars'] = get_vendor_associated_cultivars(vendor_id)
    return final_response


def get_account_associated_organizations(account_id, id_flat=False):
    return get_associations('Orgs_X_Accounts', 'Account', account_id, 'Org', id_flat=id_flat)

def get_account_associated_brands(account_id, id_flat=False):
    return get_associations('Brands_X_Accounts', 'Account', account_id, 'Brand', id_flat=id_flat)

def get_account_associated_licenses(account_id, id_flat=False):
    return get_associations('Accounts_X_Licenses', 'Licenses_Module', account_id, 'Licenses', id_flat=id_flat)

def get_account_associated_contacts(account_id, id_flat=False):
    return get_associations('Accounts_X_Contacts', 'Accounts', account_id, 'Contacts', include_fields={'roles': 'Contact_Company_Role'}, id_flat=id_flat)

def get_account_associated_cultivars_of_interest(account_id, id_flat=False):
    return get_associations('Accounts_X_Cultivars', 'Interested_Accounts', account_id, 'Cultivars_of_Interest', id_flat=id_flat)

def get_account_associations(account_id, organizations=True, brands=True, licenses=True, contacts=True, cultivars=True):
    final_response = {}
    if organizations:
        final_response['Orgs'] = get_account_associated_organizations(account_id)
    if brands:
        final_response['Brands'] = get_account_associated_brands(account_id)
    if licenses:
        final_response['Licenses'] = get_account_associated_licenses(account_id)
    if contacts:
        final_response['Contacts'] = get_account_associated_contacts(account_id)
    if cultivars:
        final_response['Cultivars'] = get_account_associated_cultivars_of_interest(account_id)
    return final_response
