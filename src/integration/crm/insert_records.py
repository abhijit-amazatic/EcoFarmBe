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
    get_licenses,
    create_records,
    update_records,
    update_license,
)


def insert_account_record(data_dict, license_db_obj, license_crm_id=None, is_update=False):
    """
    Insert account record to Zoho CRM.
    """
    d = dict()
    d.update(data_dict)
    license_profile_id = license_db_obj.license_profile.__dict__['id']
    if is_update:
        d['id'] = license_db_obj.license_profile.__dict__['zoho_crm_account_id']
        if not d['id']:
            r = search_query('Accounts', d['name'], 'Account_Name')
            if r.get('status_code') == 200:
                d['id'] = r.get('response')[0]['id']
        if d['id']:
            result = update_records('Accounts', d, is_return_orginal_data=True)
        else:
            result = create_records('Accounts', d, True)
    else:
        result = search_query('Accounts', d['name'], 'Account_Name')
        if result.get('status_code') != 200:
            result = create_records('Accounts', d, is_return_orginal_data=True)
        else:
            d['id'] = result.get('response')[0]['id']
            result = update_records('Accounts', d, True)
    if license_crm_id and result['status_code'] in [200, 201]:
        record_response = result['response']['response']['data']
        try:
            record_obj = LicenseProfile.objects.get(id=license_profile_id)
            record_obj.zoho_crm_account_id = record_response[0]['details']['id']
            record_obj.is_updated_in_crm = True
            record_obj.save()
        except KeyError as exc:
            print(exc)
            pass
        if (result['response']['orignal_data'][0].get('Licenses_List')):
            data = dict()
            data['Licenses_Module'] = record_response[0]['details']['id']
            for license in result['response']['orignal_data'][0]['Licenses_List']:
                data['Licenses'] = license
                if is_update:
                    r = update_records('Accounts_X_Licenses', [data])
                    if r.get('status_code') == 202:
                        r = create_records('Accounts_X_Licenses', [data])
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
                if r.get('status_code') == 202:
                    contact_response = create_records('Accounts_X_Contacts', request)
            else:
                contact_response = create_records('Accounts_X_Contacts', request)
    return result




def insert_vendor_record(data_dict, license_db_obj, license_crm_id=None, is_update=False):
    d = dict()
    d.update(data_dict)
    license_profile_id = license_db_obj.license_profile.__dict__['id']
    if d['profile_category'] == 'nursery':
        d['Layout_Name'] = 'vendor_cannabis_nursery'
    else:
        d['Layout_Name'] = 'vendor_cannabis'
    if is_update:
        d['id'] = license_db_obj.license_profile.__dict__['zoho_crm_vendor_id']
        if d['id']:
            r = search_query('Vendors', d['name'], 'Vendor_Name')
            if r.get('status_code') == 200:
                d['id'] = r.get('response')[0]['id']
        if d['id']:
            result = update_records('Vendors', d, True)
        else:
            result = create_records('Vendors', d, True)
    else:
        result = search_query('Vendors', d['name'], 'Vendor_Name')
        if result.get('status_code') != 200:
            result = create_records('Vendors', d, True)
        else:
            d['id'] = result.get('response')[0]['id']
            result = update_records('Vendors', d, True)
    
    if license_crm_id and result['status_code'] in [200, 201]:
        record_response = result['response']['response']['data']
        try:
            record_obj = LicenseProfile.objects.get(id=license_profile_id)
            record_obj.zoho_crm_vendor_id = record_response[0]['details']['id']
            record_obj.is_updated_in_crm = True
            record_obj.save()
        except KeyError as exc:
            print(exc)
        if (result['response']['orignal_data'][0].get('Licenses_List')):
            data = dict()
            data['Licenses_Module'] = record_response[0]['details']['id']
            for license in result['response']['orignal_data'][0]['Licenses_List']:
                data['Licenses'] = license
                if is_update:
                    r = update_records('Vendors_X_Licenses', [data])
                    if r.get('status_code') == 202:
                        r = create_records('Vendors_X_Licenses', [data])
                else:
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
            if r.get('status_code') == 202:
                contact_response = create_records('Vendors_X_Contacts', request)
        else:
            contact_response = create_records('Vendors_X_Contacts', request)
    return result


def _insert_record(record=None, license_id=None, is_update=False):
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
            licenses = get_licenses(lic_record['legal_business_name'], license_db_obj.license_number)
            d.update(license_db_obj.license_profile.__dict__)
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


            d.update({'id':licenses['id'], 'Owner':licenses['Owner']['id']})
            l.append(d['id'])
            d.update({'licenses': l})
            # farm_name = license_db_obj.license_profile.__dict__['name']
            farm_name = lic_record['legal_business_name']
            # if d['is_buyer'] == True:
            #     continue
            license_response = update_license(dba=farm_name, license=d)
            final_dict['license'] = license_response
            license_crm_id = None
            if license_response['status_code'] == 200:
                license_record_data = license_response['response']['data']
                try:
                    record_obj = License.objects.get(id=license_db_id)
                    license_crm_id = license_record_data[0]['details']['id']
                    if license_crm_id:
                        record_obj.zoho_crm_id = license_crm_id
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)

            final_dict['account'] = insert_account_record(d, license_db_obj, license_crm_id=license_crm_id, is_update=is_update)
            final_dict['vendor'] = insert_vendor_record(d, license_db_obj, license_crm_id=license_crm_id, is_update=is_update)

        except Exception as exc:
            print(exc)
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_dict['exception'] = e
        final_list[license_db_id] = final_dict
    return final_list



@app.task(queue="general")
def insert_records(id=None, is_update=False):
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
            result = search_query('Orgs', record.organization.name, 'Name')
            if result.get('status_code') == 200:
                organization_id = result.get('response')[0].get('id')
                if is_update:
                    result = update_records('Orgs', record.organization.__dict__, True)
            else:
                result = create_records('Orgs', record.organization.__dict__, True)
                if result.get('status_code') == 201:
                    organization_id = result['response']['response']['data'][0]['details']['id']

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
            record_response = _insert_record(record=record, is_update=is_update)
            final_dict.update(record_response)
            for k, response in record_response.items():
                if (brand_id or \
                    response['license']['status_code'] == 200 and \
                    response['vendor']['status_code'] in [200, 201] and \
                    organization_id):
                    data = dict()
                    resp_brand = brand_id
                    try:
                        resp_vendor = response['vendor']['response']['response']['data']
                        data['Vendor'] = resp_vendor[0]['details']['id']
                    except TypeError:
                        resp_vendor = response['vendor']['response'][0]
                        data['Vendor'] = resp_vendor['id']
                    data['Org'] = organization_id
                    data['Brand'] = brand_id
                    if is_update:
                        r = update_records('Orgs_X_Vendors', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Orgs_X_Vendors', [data])
                        final_dict['org_vendor'] = r

                        r = update_records('Orgs_X_Brands', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Orgs_X_Brands', [data])
                        final_dict['org_brand'] = r

                        r = update_records('Brands_X_Vendors', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Brands_X_Vendors', [data])
                        final_dict['brand_vendor'] = r
                    else:
                        r = create_records('Orgs_X_Vendors', [data])
                        final_dict['org_vendor'] = r
                        r = create_records('Orgs_X_Brands', [data])
                        final_dict['org_brand'] = r
                        r = create_records('Brands_X_Vendors', [data])
                        final_dict['brand_vendor'] = r

                if (brand_id or \
                    response['license']['status_code'] == 200 and \
                    response['account']['status_code'] in [200, 201] and organization_id):
                    data = dict()
                    try:
                        resp_account = response['account']['response']['response']['data']
                        data['Account'] = resp_account[0]['details']['id']
                    except TypeError:
                        resp_account = response['account']['response'][0]
                        data['Account'] = resp_account['id']
                    data['Org'] = organization_id
                    data['Brand'] = brand_id
                    if is_update:
                        r = update_records('Orgs_X_Accounts', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Orgs_X_Accounts', [data])
                        final_dict['org_account'] = r

                        r = update_records('Orgs_X_Brands', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Orgs_X_Brands', [data])
                        final_dict['org_brand'] = r

                        r = update_records('Brands_X_Accounts', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Brands_X_Accounts', [data])
                        final_dict['brand_account'] = r
                    else:
                        r = create_records('Orgs_X_Accounts', [data])
                        final_dict['org_account'] = r
                        r = create_records('Orgs_X_Brands', [data])
                        final_dict['org_brand'] = r
                        r = create_records('Brands_X_Accounts', [data])
                        final_dict['brand_account'] = r

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
