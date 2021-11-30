from logging import exception
import sys
import traceback

from core.celery import app
from brand.models import (
    Brand,
    License,
    LicenseProfile,
    Organization,
)
from .core import (
    search_query,
    get_crm_obj,
    get_record,
    get_licenses,
    create_records,
    update_records,
    update_license,
    get_lookup_id,
    update_in_crm,
)
from .get_records import(
    get_associations,
    get_account_associated_contacts,
    get_vendor_associated_contacts,
    get_account_associated_organizations,
    get_account_associated_brands,
    get_vendor_associated_brands,
    get_vendor_associated_organizations,
)


def get_associated_vendor(license_crm_id,):
    vendor_id = None
    vendor = search_query('Vendors_X_Licenses', license_crm_id, 'Licenses')
    if vendor['status_code'] == 200:
        try:
            vendor = vendor['response'][0]['Licenses_Module']
            vendor_id = vendor['id']
        except Exception:
            pass
    return vendor_id

def get_associated_account(license_crm_id):
    account_id = None
    account = search_query('Accounts_X_Licenses', license_crm_id, 'Licenses')
    if account['status_code'] == 200:
        try:
            account = account['response'][0]['Licenses_Module']
            account_id = account['id']
        except Exception:
            pass
    return account_id


def create_employees_in_crm(employee_list):
    """
    Create contacts in Zoho CRM.
    """
    cd = {
        'first_name': 'employee_name',
        'last_name': 'employee_name',
        'full_name': 'employee_name',
        'email': 'employee_email',
        'phone': 'phone',
    }
    contacts = list()
    try:
        for e in employee_list:
            user = {k: (e.get(v) or '') for k, v in cd.items()}
            if user.get('email'):
                
                full_name = user['full_name'].split()
                user['first_name'] = ' '.join(full_name[0:-1])
                user['last_name'] = full_name[-1]

                r = create_records('Contacts', [user])
                if r['status_code'] in (201, 202):
                    try:
                        contact_id = r['response']['data'][0]['details']['id']
                    except Exception:
                        pass
                    else:
                        contacts.append({
                            'roles': e.get('roles', []),
                            'contact_crm_id': contact_id,
                        })
        return contacts
    except IndexError:
        return []
    except TypeError:
        return []

CONTACT_ASSOCIATION_MODULE_MAP = {
    "Accounts_X_Contacts": {
        "contact_field": "Contacts",
        "role_field": "Contact_Company_Role",
        "profile_field": "Accounts",
    },
    "Vendors_X_Contacts": {
        "contact_field": "Contact",
        "role_field": "Contact_Company_Role",
        "profile_field": "Vendor",
    },
}


def create_or_update_contact_associations(module, crm_profile_id, employee_list, is_update=False):
    final_response = dict()
    try:
        contact_field = CONTACT_ASSOCIATION_MODULE_MAP[module]["contact_field"]
        role_field = CONTACT_ASSOCIATION_MODULE_MAP[module]["role_field"]
        profile_field = CONTACT_ASSOCIATION_MODULE_MAP[module]["profile_field"]

        contacts_list = create_employees_in_crm(employee_list)
        associated_contacts = get_account_associated_contacts(crm_profile_id)
        associated_contacts = {
            x['id']: {'roles': x['roles'], 'linking_obj_id': x['linking_obj_id']} for x in associated_contacts
        }
        update_request = list()
        create_request = list()
        for contact in contacts_list:
            contact_id = contact['contact_crm_id']
            if contact_id in associated_contacts:
                if is_update:
                    data = dict()
                    insert = True
                    for j in update_request:
                        if j.get(contact_field) == contact_id:
                            if contact.get('roles'):
                                j[role_field].add(*contact['roles'])
                            insert = False
                    if insert:
                        data['id'] = associated_contacts[contact_id]['linking_obj_id']
                        data[contact_field] = contact_id
                        data[role_field] = set(associated_contacts[contact_id]['roles'] or [])
                        if contact.get('roles'):
                            data[role_field].add(*contact['roles'])
                        data[profile_field] = crm_profile_id
                        update_request.append(data)
            else:
                data = dict()
                insert = True
                for j in create_request:
                    if j.get(contact_field) == contact_id:
                        if contact.get('roles'):
                            j[role_field].add(*contact['roles'])
                        insert = False
                if insert:
                    data[contact_field] = contact_id
                    data[role_field] = set(contact.get('roles') or [])
                    data[profile_field] = crm_profile_id
                    create_request.append(data)
        if is_update and update_request:
            update_request = [{k: list(v) if isinstance(v, set) else v  for k, v in r.items()} for r in update_request]
            final_response['update'] = update_records(module, update_request)
        if create_request:
            create_request = [{k: list(v) if isinstance(v, set) else v  for k, v in r.items()} for r in create_request]
            final_response['create'] = create_records(module, create_request)

    except Exception as exc:
        print(exc)
        debug_vars = (
            'associated_contacts', 'contact', 'create_request', 'update_request', 'contact_id',
            'crm_profile_id', 'employee_list', ''
        )
        locals_data = {k: v for k, v in locals().items() if k in debug_vars}
        exc_info = sys.exc_info()
        e = ''.join(traceback.format_exception(*exc_info))
        final_response['exception'] = e
        final_response['local_vars'] = locals_data
    return final_response


def insert_account_record(data_dict, license_db_obj, license_crm_id=None, account_crm_id=None, is_update=False):
    """
    Insert account record to Zoho CRM.
    """
    final_response = dict()

    d = dict()
    d.update(data_dict)
    license_profile_id = license_db_obj.license_profile.__dict__['id']

    d['id'] = account_crm_id
    if not d['id']:
        d['id'] = license_db_obj.license_profile.__dict__['zoho_crm_account_id']

    if not d['id'] and license_crm_id:
        license_response = get_record('Licenses', license_crm_id)
        if license_response.get('status_code') == 200:
            license_record = license_response.get('response', {}).get(license_crm_id, {})
            d['id'] = get_lookup_id(license_record, 'Account_Name_Lookup')

    if not d['id']:
        r = search_query('Accounts', d['legal_business_name'], 'Account_Business_DBA')
        if r.get('status_code') == 200:
            d['id'] = r.get('response')[0]['id']

    if not d['id'] and license_crm_id:
        d['id'] = get_associated_account(license_crm_id)

    if not d['id']:
        r = search_query('Accounts', d['name'], 'Account_Name')
        if r.get('status_code') == 200:
            d['id'] = r.get('response')[0]['id']

    if d['id']:
        if 'Owner' in d:
            data = {}
            data.update(d)
            data.pop('Owner')
            d = data
        result = update_records('Accounts', d, is_return_orginal_data=True)
    else:
        result = create_records('Accounts', d, is_return_orginal_data=True)

    final_response['account'] = result

    if license_crm_id and result['status_code'] in [200, 201]:
        record_response = result['response']['response']['data']
        account_id = record_response[0]['details']['id']
        record_obj = LicenseProfile.objects.get(id=license_profile_id)
        if account_id and (not record_obj.zoho_crm_account_id or account_crm_id):
            record_obj.zoho_crm_account_id = account_id
        record_obj.is_account_updated_in_crm = True
        record_obj.save()

        final_response['Accounts_X_Licenses'] = dict()
        try:
            if (result['response']['orignal_data'][0].get('Licenses_List')):
                data = dict()
                data['Licenses_Module'] = account_id
                for license in result['response']['orignal_data'][0]['Licenses_List']:
                    data['Licenses'] = license
                    if is_update:
                        r = update_records('Accounts_X_Licenses', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Accounts_X_Licenses', [data])
                    else:
                        r = create_records('Accounts_X_Licenses', [data])
                    final_response['Accounts_X_Licenses'] = r
        except Exception as exc:
            print(exc)
            debug_vars = ('data', 'account_id',)
            locals_data = {k: v for k, v in locals().items() if k in debug_vars}
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_response['Accounts_X_Licenses']['exception'] = e
            final_response['Accounts_X_Licenses']['local_vars'] = locals_data

        final_response['Accounts_X_Cultivars'] = dict()
        try:
            if result['response']['orignal_data'][0].get('Cultivars_List'):
                data = dict()
                data['Interested_Accounts'] = account_id
                for j in result['response']['orignal_data'][0]['Cultivars_List']:
                    r = search_query('Cultivars', j, 'Name')
                    if r['status_code'] == 200:
                        data['Cultivars_of_Interest'] = r['response'][0]['id']
                        r = create_records('Accounts_X_Cultivars', [data])
                    final_response['Accounts_X_Cultivars'][j] = r
        except Exception as exc:
            print(exc)
            debug_vars = ('data', 'vendor_id')
            locals_data = {k: v for k, v in locals().items() if k in debug_vars}
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_response['Accounts_X_Cultivars']['exception'] = e
            final_response['Accounts_X_Cultivars']['local_vars'] = locals_data

        contact_list = license_db_obj.get_contacts()
        final_response['Accounts_X_Contacts'] = create_or_update_contact_associations(
            'Accounts_X_Contacts', account_id, contact_list, is_update=is_update
        )

    else:
        record_obj = LicenseProfile.objects.get(id=license_profile_id)
        record_obj.is_account_updated_in_crm = False
        record_obj.save()

    return final_response


def insert_vendor_record(data_dict, license_db_obj, license_crm_id=None, vendor_crm_id=None, is_update=False):
    final_response = dict()

    d = dict()
    d.update(data_dict)
    license_profile_id = license_db_obj.license_profile.__dict__['id']
    if d['profile_category'] == 'nursery':
        d['Layout_Name'] = 'vendor_cannabis_nursery'
    else:
        d['Layout_Name'] = 'vendor_cannabis'

    d['id'] = vendor_crm_id
    if not d['id']:
        d['id'] = license_db_obj.license_profile.__dict__['zoho_crm_vendor_id']

    if not d['id'] and license_crm_id:
        license_response = get_record('Licenses', license_crm_id)
        if license_response.get('status_code') == 200:
            license_record = license_response.get('response', {}).get(license_crm_id, {})
            d['id'] = get_lookup_id(license_record, 'Vendor_Name_Lookup')

    if not d['id']:
        r = search_query('Vendors', d['legal_business_name'], 'Legal_Entity_Names')
        if r.get('status_code') == 200:
            d['id'] = r.get('response')[0]['id']

    if not d['id']:
        r = search_query('Vendors', d['name'], 'Vendor_Name')
        if r.get('status_code') == 200:
            d['id'] = r.get('response')[0]['id']

    if not d['id'] and license_crm_id:
        d['id'] = get_associated_vendor(license_crm_id)

    if d['id']:
        if 'Owner' in d:
            data = {}
            data.update(d)
            data.pop('Owner')
            d = data
        result = update_records('Vendors', d, is_return_orginal_data=True)
    else:
        result = create_records('Vendors', d, is_return_orginal_data=True)

    final_response['vendor'] = result

    if license_crm_id and result['status_code'] in [200, 201]:
        record_response = result['response']['response']['data']
        vendor_id = record_response[0]['details']['id']

        record_obj = LicenseProfile.objects.get(id=license_profile_id)
        if vendor_id and (not record_obj.zoho_crm_vendor_id or vendor_crm_id):
            record_obj.zoho_crm_vendor_id = vendor_id
        record_obj.is_vendor_updated_in_crm = True
        record_obj.save()


        final_response['Vendors_X_Licenses'] = dict()
        try:
            if (result['response']['orignal_data'][0].get('Licenses_List')):
                data = dict()
                data['Licenses_Module'] = vendor_id
                for license in result['response']['orignal_data'][0]['Licenses_List']:
                    data['Licenses'] = license
                    if is_update:
                        r = update_records('Vendors_X_Licenses', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Vendors_X_Licenses', [data])
                    else:
                        r = create_records('Vendors_X_Licenses', [data])
                    final_response['Vendors_X_Licenses'] = r
        except Exception as exc:
            print(exc)
            debug_vars = ('data', 'vendor_id')
            locals_data = {k: v for k, v in locals().items() if k in debug_vars}
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_response['Vendors_X_Licenses']['exception'] = e
            final_response['Vendors_X_Licenses']['local_vars'] = locals_data


        final_response['Vendors_X_Cultivars'] = dict()
        try:
            if result['response']['orignal_data'][0].get('Cultivars_List'):
                data = dict()
                data['Cultivar_Associations'] = vendor_id
                for j in result['response']['orignal_data'][0]['Cultivars_List']:
                    r = search_query('Cultivars', j, 'Name')
                    if r['status_code'] == 200:
                        data['Cultivars'] = r['response'][0]['id']
                        r = create_records('Vendors_X_Cultivars', [data])
                    final_response['Vendors_X_Cultivars'][j] = r
        except Exception as exc:
            print(exc)
            debug_vars = ('data', 'vendor_id')
            locals_data = {k: v for k, v in locals().items() if k in debug_vars}
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_response['Vendors_X_Cultivars']['exception'] = e
            final_response['Vendors_X_Cultivars']['local_vars'] = locals_data

        contact_list = license_db_obj.get_contacts()
        final_response['Vendors_X_Contacts'] = create_or_update_contact_associations(
            'Vendors_X_Contacts', vendor_id, contact_list, is_update=is_update
        )

    else:
        record_obj = LicenseProfile.objects.get(id=license_profile_id)
        record_obj.is_vendor_updated_in_crm = False
        record_obj.save()

    return final_response


def get_crm_license(license_number):
    """
    Get license from Zoho CRM.
    """
    licenses = search_query('Licenses', license_number, 'Name')
    if licenses['status_code'] == 200:
        for license in licenses['response']:
            if license.get('Name') == license_number:
                return license

def get_crm_license_by_id(obj_id):
    """
    Get license from Zoho CRM.
    """
    licenses = search_query('Licenses', obj_id, 'id')
    if licenses['status_code'] == 200:
        for license in licenses['response']:
            if license.get('id') == obj_id:
                return license

def _insert_record(record=None, license_id=None, account_crm_id=None, vendor_crm_id=None, is_update=False):
    """
    Insert record to Zoho CRM.
    """
    if license_id:
        licenses = [License.objects.select_related().get(id=license_id).__dict__]
    else:
        licenses = [record.__dict__]
    final_list = dict()
    for lic_record in licenses:
        try:
            final_dict = dict()
            l = list()
            d = dict()
            d.update(lic_record)
            license_db_id = lic_record['id']
            d.update({'license_db_id': license_db_id})
            license_db_obj = License.objects.select_related().get(id=license_db_id)

            crm_license = {}
            if license_db_obj.zoho_crm_id:
                crm_license = get_crm_license_by_id(license_db_obj.zoho_crm_id)
            if not crm_license:
                crm_license = get_licenses(lic_record['legal_business_name'], license_db_obj.license_number)
            if not crm_license:
                crm_license = get_crm_license(license_db_obj.license_number)

            d.update(license_db_obj.license_profile.__dict__)
            license_db_obj.license_profile.is_account_updated_in_crm = False
            license_db_obj.license_profile.is_vendor_updated_in_crm = False
            license_db_obj.license_profile.save()

            try:
                d.update(license_db_obj.profile_contact.profile_contact_details)
            except Exception:
                pass
            try:
                for k, v in license_db_obj.cultivation_overview.__dict__.items():
                    d.update({'co.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db_obj.financial_overview.__dict__.items():
                    d.update({'fo.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db_obj.crop_overview.__dict__.items():
                    d.update({'cr.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db_obj.nursery_overview.__dict__.items():
                    d.update({'no.' + k:v})
            except Exception:
                pass
            try:
                d.update(license_db_obj.program_overview.__dict__)
            except Exception:
                pass

            try:
                d["employees"].update(license_db_obj.get_contacts())
            except Exception:
                pass

            d.update({'id':crm_license['id'], 'Owner':crm_license['Owner']['id']})
            l.append(d['id'])
            d.update({'licenses': l})
            # farm_name = license_db_obj.license_profile.__dict__['name']
            farm_name = lic_record['legal_business_name']
            # if d['is_buyer'] == True:
            #     continue
            license_response = update_license(dba=farm_name, license=d, is_return_orginal_data=True)
            final_dict['license'] = license_response
            license_crm_id = crm_license['id']
            if license_response['status_code'] == 200:
                license_record_data = license_response['response']['response']['data']
                try:
                    record_obj = License.objects.get(id=license_db_id)
                    if license_record_data[0]['details']['id']:
                        license_crm_id = license_record_data[0]['details']['id']
                        if license_crm_id and not record_obj.zoho_crm_id:
                            record_obj.zoho_crm_id = license_crm_id
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
            else:
                record_obj = License.objects.get(id=license_db_id)
                if license_crm_id and not record_obj.zoho_crm_id:
                    record_obj.zoho_crm_id = license_crm_id
                record_obj.is_updated_in_crm = False
                record_obj.save()

            final_dict.update(insert_account_record(d, license_db_obj, license_crm_id=license_crm_id, account_crm_id=account_crm_id, is_update=is_update))
            final_dict.update(insert_vendor_record(d, license_db_obj, license_crm_id=license_crm_id, vendor_crm_id=vendor_crm_id, is_update=is_update))
            if not d.get('zoho_crm_vendor_id') or not d.get('zoho_crm_account_id'):
                update_in_crm('Licenses', license_db_obj.id)
        except Exception as exc:
            print(exc)
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_dict['exception'] = e
        final_list[license_db_id] = final_dict
    return final_list



def insert_records(id=None, is_update=False, account_crm_id=None, vendor_crm_id=None,):
    """
    Insert Vendors into Zoho CRM.
    """
    brand_id = None
    final_list = dict()
    if id:
        records = License.objects.filter(id=id).select_related()
    else:
        records = License.objects.filter(is_updated_in_crm=False).select_related()
    for record in records:
        final_dict = dict()
        try:
            organization_id = None
            try:
                result = search_query('Orgs', record.organization.name, 'Name')
                if result.get('status_code') == 200:
                    organization_id = result.get('response')[0].get('id')
                    if is_update:
                        result = update_records('Orgs', record.organization.__dict__, True)
                else:
                    result = create_records('Orgs', record.organization.__dict__, True)
                    if result.get('status_code') == 201:
                        organization_id = result['response']['response']['data'][0]['details']['id']
            except Exception as exc:
                print(exc)

            brand_id = None
            try:
                result = search_query('Brands', record.brand.brand_name, 'Name')
                if result.get('status_code') == 200:
                    brand_id = result['response'][0].get('id')
                    if is_update:
                        result = update_records('Brands', record.brand.__dict__, True)
                else:
                    result = create_records('Brands', record.brand.__dict__, True)
                    if result.get('status_code') == 201:
                        brand_id = result['response']['response']['data'][0]['details']['id']
            except Exception as exc:
                print(exc)

            final_dict['org'] = organization_id
            final_dict['brand'] = brand_id
            if brand_id:
                try:
                    record_obj = Brand.objects.get(id=record.brand_id)
                    record_obj.zoho_crm_id = brand_id
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
            if organization_id:
                try:
                    record_obj = Organization.objects.get(id=record.organization_id)
                    record_obj.zoho_crm_id = organization_id
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)

            record_response = _insert_record(record=record, account_crm_id=account_crm_id, vendor_crm_id=vendor_crm_id, is_update=is_update)
            final_dict.update(record_response)

            for k, response in record_response.items():
                if response['license']['status_code'] == 200:
                    data = dict()
                    account_id = None
                    vendor_id = None

                    if response['account']['status_code'] in [200, 201]:
                        try:
                            resp_account = response['account']['response']['response']['data']
                            account_id = resp_account[0]['details']['id']
                        except TypeError:
                            resp_account = response['account']['response'][0]
                            account_id = resp_account['id']

                    if response['vendor']['status_code'] in [200, 201]:
                        try:
                            resp_vendor = response['vendor']['response']['response']['data']
                            vendor_id = resp_vendor[0]['details']['id']
                        except TypeError:
                            resp_vendor = response['vendor']['response'][0]
                            vendor_id = resp_vendor['id']

                    data['Account'] = account_id
                    data['Vendor'] = vendor_id
                    data['Org'] = organization_id
                    data['Brand'] = brand_id

                    if account_id:
                        if organization_id:
                            associated_org_ids = get_account_associated_organizations(account_id, id_flat=True)
                            if organization_id not in associated_org_ids:
                                r = create_records('Orgs_X_Accounts', [data])
                            else:
                                r = {'msg': 'Association already exist'}
                            final_dict['org_account'] = r
                        if brand_id:
                            associated_brand_ids = get_account_associated_brands(account_id, id_flat=True)
                            if brand_id not in associated_brand_ids:
                                r = create_records('Brands_X_Accounts', [data])
                            else:
                                r = {'msg': 'Association already exist'}
                            final_dict['brand_account'] = r

                    if vendor_id:
                        if organization_id:
                            associated_org_ids = get_vendor_associated_organizations(vendor_id, id_flat=True)
                            if organization_id not in associated_org_ids:
                                r = create_records('Orgs_X_Vendors', [data])
                            else:
                                r = {'msg': 'Association already exist'}
                            final_dict['org_vendor'] = r
                        if brand_id:
                            associated_brand_ids = get_vendor_associated_brands(vendor_id, id_flat=True)
                            if brand_id not in associated_brand_ids:
                                r = create_records('Brands_X_Vendors', [data])
                            else:
                                r = {'msg': 'Association already exist'}
                            final_dict['brand_vendor'] = r

                    if organization_id and brand_id:
                        org_associated_brand_ids = get_associations('Orgs_X_Brands', 'Org', organization_id, 'Brand', id_flat=True)
                        if brand_id not in org_associated_brand_ids:
                            r = create_records('Orgs_X_Brands', [data])
                        else:
                            r = {'msg': 'Association already exist'}
                        final_dict['org_brand'] = r

        except Exception as exc:
            print(exc)
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_dict['exception'] = e
        final_list[record.id] = final_dict
        record.refresh_from_db()
        record.crm_output = {'output': final_dict}
        record.save()
    return final_list
