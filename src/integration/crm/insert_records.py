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


def insert_record(record=None, is_update=False, id=None, is_single_user=False):
    """
    Insert record to Zoho CRM.
    """
    if id and is_single_user:
        licenses = [License.objects.select_related().get(id=id).__dict__]
    else:
        licenses = [record.__dict__]
    final_list = dict()
    for i in licenses:
        try:
            final_dict = dict()
            d = dict()
            l = list()
            d.update(i)
            license_db_id = i['id']
            d.update({'license_db_id': license_db_id})
            license_db = License.objects.select_related().get(id=license_db_id)
            licenses = get_licenses(i['legal_business_name'], license_db.license_number)
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
                for k, v in license_db.nursery_overview.__dict__.items():
                    d.update({'no.' + k:v})
            except Exception:
                pass
            try:
                d.update(license_db.program_overview.__dict__)
            except Exception:
                pass
            d.update({'id':licenses['id'], 'Owner':licenses['Owner']['id']})
            l.append(d['id'])
            d.update({'licenses': l})
            if id and is_single_user and is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_vendor_id']
            # farm_name = license_db.license_profile.__dict__['name']
            farm_name = i['legal_business_name']
            # if d['is_buyer'] == True:
            #     continue
            response = update_license(dba=farm_name, license=d)
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
            if i['profile_category'] == 'nursery':
                d['Layout_Name'] = 'vendor_cannabis_nursery'
            else:
                d['Layout_Name'] = 'vendor_cannabis'
            if is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_vendor_id']
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
            final_dict['vendor'] = result
            print(result)
            if response['status_code'] == 200 and result['status_code'] in [200, 201]:
                record_response = result['response']['response']['data']
                try:
                    record_obj = LicenseProfile.objects.get(id=vendor_id)
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
        except Exception as exc:
            print(exc)
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_dict['exception'] = e
        final_list[license_db_id] = final_dict
    return final_list



@app.task(queue="general")
def insert_vendors(id=None, is_update=False, is_single_user=False):
    """
    Insert Vendors into Zoho CRM.
    """
    brand_id = None
    if is_single_user:
        return insert_record(id=id, is_update=is_update, is_single_user=is_single_user)
    else:
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
                record_response = insert_record(record=record, is_update=is_update, is_single_user=is_single_user)
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



def insert_account_record(record=None, is_update=False, id=None, is_single_user=False):
    """
    Insert account to Zoho CRM.
    """
    if id and is_single_user:
        licenses = [License.objects.select_related().get(id=id).__dict__]
    else:
        licenses = [record.__dict__]
    final_list = dict()
    for i in licenses:
        try:
            final_dict = dict()
            l = list()
            d = dict()
            d.update(i)
            license_db_id= i['id']
            d.update({'license_db_id': license_db_id})
            license_db = License.objects.select_related().get(id=license_db_id)
            licenses = get_licenses(i['legal_business_name'], license_db.license_number)
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
            d.update({'id':licenses['id'], 'Owner':licenses['Owner']['id']})
            l.append(d['id'])
            d.update({'licenses': l})    
            if id and is_single_user and is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_account_id']
            # farm_name = license_db.license_profile.__dict__['name']
            farm_name = i['legal_business_name']
            # if d['is_seller'] == True:
            #         continue
            response = update_license(dba=farm_name, license=d)
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
                d['id'] = license_db.license_profile.__dict__['zoho_crm_account_id']
                if d['id']:
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
            final_dict['account'] = result
            if response['status_code'] == 200 and result['status_code'] in [200, 201]:
                record_response = result['response']['response']['data']
                try:
                    record_obj = LicenseProfile.objects.get(id=vendor_id)
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
        except Exception as exc:
            print(exc)
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_dict['exception'] = e
        final_list[license_db_id] = final_dict
    return final_list

@app.task(queue="general")
def insert_accounts(id=None, is_update=False, is_single_user=False):
    """
    Insert new accounts in Zoho CRM.
    """
    brand_id = None
    if is_single_user:
        return insert_account_record(id=id, is_single_user=is_single_user)
    else:
        final_list = dict()
        if id:
            records = License.objects.filter(id=id).select_related()
        else:
            records = License.objects.filter(is_updated_in_crm=False).select_related()
        for record in records:
            final_dict = dict()
            try:
                if is_update:
                    result = search_query('Orgs', record.organization.name, 'Name')
                    if result.get('status_code') == 200:
                        organization_id = result.get('response')[0].get('id')
                        result = update_records('Orgs', record.organization.__dict__, True)
                    else:
                        result = create_records('Orgs', record.organization.__dict__, True)
                    if result.get('status_code') in [200, 201]:
                        try:
                            organization_id = result['response'][0]['id']
                        except KeyError:
                            organization_id = result['response']['response']['data'][0]['details']['id']
                else:
                    result = search_query('Orgs', record.organization.name, 'Name')
                    if result.get('status_code') == 200:
                        organization_id = result['response'][0]['id']
                    else:
                        result = create_records('Orgs', record.organization.__dict__, True)
                        if result.get('status_code') == 201:
                            organization_id = result['response']['response']['data'][0]['details']['id']
                try:
                    if is_update:
                        result = search_query('Brands', record.brand.brand_name, 'Name')
                        if result.get('status_code') == 200:
                            result = update_records('Brands', record.brand.__dict__, True)
                        else:
                            result = create_records('Brands', record.brand.__dict__, True)
                        if result.get('status_code') in [200, 201]:
                            try:
                                brand_id = result['response'][0]['id']
                            except KeyError:
                                brand_id = result['response']['response']['data'][0]['details']['id']
                    else:
                        result = search_query('Brands', record.brand.brand_name, 'Name')
                        if result.get('status_code') == 200:
                            brand_id = result['response'][0]['id']
                        else:
                            result = create_records('Brands', record.brand.__dict__, True)
                            if result.get('status_code') == 201:
                                brand_id = result['response']['response']['data'][0]['details']['id']
                except Exception as exc:
                    print(exc)
                    brand_id = None
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
                record_response = insert_account_record(record=record, is_update=is_update, is_single_user=is_single_user)
                final_dict.update(record_response)
                for k, response in record_response.items():
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
