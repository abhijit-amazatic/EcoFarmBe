"""
BCC license library.
"""
import json
import requests
from datetime import (datetime, )
from core.settings import (BCC_APP_ID, BCC_APP_KEY, LICENSE_LAYOUT)
from integration.crm import (search_query, get_crm_obj, )

def get_licenses():
    """
    Get licenses from BCC database.
    """
    url = "https://iservices.dca.ca.gov/api/bcclicenseread/getAllBccLicenses"
    headers = dict()
    headers['app_id'] = BCC_APP_ID
    headers['app_key'] = BCC_APP_KEY
    response = requests.get(url, headers=headers)
    return response.json()

def get_dcc_pages():
    url = 'https://as-cdt-pub-vip-cannabis-ww-p-002.azurewebsites.net/licenses/filteredSearch?pageSize=&pageNumber='
    return requests.get(url).json()["metadata"]["totalPages"]

def get_dcc_licenses(page):
    url = 'https://as-cdt-pub-vip-cannabis-ww-p-002.azurewebsites.net/licenses/filteredSearch?pageSize=&pageNumber='
    res = requests.get(url + str(page))
    return res.json()["data"]

def get_license_dict():
    return {
    "Layout": "layout_parse",
    "Name": "licenseNumber",
	"License_Type": "licenseType_parse",
	"Issue_Date": "issuedDate_parse",
	"Premises_City": "premiseCity",
	"Premises_State": "premiseState_parse",
	"Premises_Zipcode": "premiseZip",
	"Premises_County": "premiseCounty",
	"License_Status": "licenseStatus",
	"Business_Structure": "businessStructure",
	"Expiration_Date": "expiryDate_parse",
	"Legal_Business_Name": "businessName",
	"Business_DBA": "businessDBA",
	"Owner_First_Name": "businessOwner_parse",
	"Owner_Last_Name": "businessOwner_parse",
	"License_Website": "website",
	"Phone_Number": "phone",
	"License_Email": "email",
    "Verified_Date": "verified_date_parse"
    }

def parse_field(license, key, value):
    """
    Return parsed field.
    """
    v = license.get(value) 
    if value.startswith('businessOwner'):
        if v == 'null':
            return None
        if key == 'Owner_First_Name':
            return v.split(' ')[0]
        else:
            return v.split(' ')[1]
    if value.startswith('issuedDate') or value.startswith('expiryDate'):
        return datetime.strptime(v, "%m/%d/%Y").date()
    if value.startswith('licenseType'):
        license_types = {
            "Cannabis - Retailer License": "Retailer - Storefront",
            "Cannabis - Retailer Temporary License": "Retailer - Storefront",
            "Commercial -  Retailer": "Retailer - Storefront",
            "Cannabis - Retailer Nonstorefront License": "Retailer - Delivery",
            "Cannabis - Retailer Nonstorefront Temporary License": "Retailer - Delivery",
            "Commercial -  Retailer - Non-Storefront": "Retailer - Delivery",
            "Cannabis - Microbusiness License": "Microbusiness",
            "Cannabis - Microbusiness Temporary License": "Microbusiness",
            "Commercial -  Microbusiness": "Microbusiness",
            "Cannabis - Distributor License": "Distributor",
            "Cannabis - Distributor Temporary License": "Distributor",
            "Commercial -  Distributor": "Distributor",
            "Cannabis - Distributor-Transport Only License": "Distributor Transport Only",
            "Cannabis - Distributor-Transport Only Temporary License": "Distributor Transport Only",
            "Commercial -  Distributor - Transport Only": "Distributor Transport Only", 
            "Cannabis - Event Organizer License": "Event Organizer",
            "Commercial -  Event Organizer": "Event Organizer",
            "Cannabis - Testing Laboratory License": "Testing Laboratory",
            "Commercial -  Testing Laboratory": "Testing Laboratory"
        }
        if license_types.get(v):
            return license_types.get(v)
        return v
    if value.startswith('premiseState'):
        premise_state = {
            "CA":"California",
        }
        return premise_state.get(v, v)
    if value.startswith('layout'):
        try:
            license_layout = json.loads(LICENSE_LAYOUT)
        except Exception:
            license_layout = LICENSE_LAYOUT
        return license_layout['non-cultivar']
    if value.startswith('verified_date'):
        return datetime.now().date()

def get_all_licenses():
    """
    Get all licenses from crm.
    """
    crm_obj = get_crm_obj()
    response = dict()
    records = crm_obj.get_records('Licenses')
    page = 1
    if records.get('status_code') == 200:
        while records.get('response').get('info').get('more_records'):
            for i in records.get('response').get('data'):
                response[i['Name']] = i['id']
            records = crm_obj.get_records('Licenses', page=page)
            page += 1
    return response

def licenses_dcc_to_crm():
    """
    Post licenses from DCC to CRM.
    """
    crm_obj = get_crm_obj()
    response_update = list()
    total_pages = get_dcc_pages()
    license_data_dict = get_all_licenses()
    request_update = list()

    for page in range(1,total_pages+1):    
        licenses = get_dcc_licenses(page)
        for license in licenses:
            req = dict()
            if license.get('licenseNumber') in license_data_dict:
                v = license.get('activity')
                if v:
                    if v == 'Data Not Available':
                        v = []
                    else:
                        v = [i.strip() for i in v.split(",")]
                if v:
                    req['Activities'] = v
                    license_id = license_data_dict.get(license.get('licenseNumber'))
                    if license_id:
                        req['id'] = license_id
                        request_update.append(req)
    i = 0
    while len(request_update) > i:
        response_update.append(crm_obj.update_records("Licenses", request_update[i: i+100]))
        i += 100
    return response_update

def post_licenses_to_crm():
    """
    Post licenses from BCC to CRM.
    """
    crm_obj = get_crm_obj()
    request_update = list()
    request_create = list()
    licenses = get_licenses()
    license_dict = get_license_dict()
    license_data_dict = get_all_licenses()
    for license in licenses:
        req = dict()
        for k, v in license_dict.items():
            if v.endswith('_parse'):
                req[k] = parse_field(license, k, v.split('_parse')[0])
            else:
                req[k] = license.get(v)
        license_id = license_data_dict.get(license.get('licenseNumber'))
        if license_id:
            req['id'] = license_id
            request_update.append(req)
        else:
            request_create.append(req)
    i = 0
    response_create = response_update = list()
    while len(request_create) > i:
        response_create.append(crm_obj.insert_records("Licenses", request_create[i: i+100]))
        i += 100
    i = 0
    response_create = response_update = list()
    while len(request_update) > i:
        response_update.append(crm_obj.update_records("Licenses", request_update[i: i+100]))
        i += 100
    licenses_dcc_to_crm()
    return response_create, response_update 
    
