"""
BCC license library.
"""
import requests
from datetime import (datetime, )
from core.settings import (BCC_APP_ID, BCC_APP_KEY)
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

def get_license_dict():
    return {
    "Name": "licenseNumber",
	"License_Type": "licenseType",
	"Issue_Date": "issuedDate_parse",
	"Premises_City": "premiseCity",
	"Premises_State": "premiseState",
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

def post_licenses_to_crm():
    """
    Post licenses from BCC to CRM.
    """
    crm_obj = get_crm_obj()
    request_update = list()
    request_create = list()
    licenses = get_licenses()
    license_dict = get_license_dict()
    for license in licenses:
        data = crm_obj.search_record('Licenses', license.get('licenseNumber'), 'Name')
        req = dict()
        for k, v in license_dict.items():
            if v.endswith('_parse'):
                req[k] = parse_field(license, k, v.split('_parse')[0])
            else:
                req[k] = license.get(v)
        if data.get('response') and len(data.get('response')) > 0:
            req['id'] = data.get('response')[0].get('id')
            request_update.append(req)
        else:
            request_create.append(req)
    response_create = crm_obj.insert_records("Licenses", request_create)
    response_update = crm_obj.update_records("Licenses", request_update)
    return response_create, response_update
    