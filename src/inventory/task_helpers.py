from integration.crm import (get_crm_obj, search_query, create_records, update_records)


accounts_to_vendors_dict = {
    'id': 'Associated_Account_Record',
    'About_Company': 'About_Company',
    'Account_Name': 'Vendor_Name',
    'Account_Business_DBA': 'Legal_Entity_Names',
    'Tier_Selection': 'Program_Selection',
    'Record_Image': 'Record_Image',
    'Annual_Revenue': 'Annual_Revenue',
    # 'Associated_Vendor_Record': '',
    'Bank_Account_Number': 'Bank_Account_Number',
    'Bank_City': 'Bank_City',
    'Bank_Country': 'Bank_Country',
    'Bank_Name': 'Bank_Name',
    'Bank_Routing_Number': 'Bank_Routing_Number',
    'Bank_States': 'Bank_State',
    'Bank_Street': 'Bank_Street',
    'Bank_Zip_Code': 'Bank_Zip_Code',
    'Billing_City': 'Billing_City',
    'Billing_Code': 'Billing_Zip_Code',
    # 'Billing_Company_Name': '',
    'Billing_Country': 'Billing_Country',
    'Billing_Notes': 'Billing_Notes',
    'Billing_State': 'Billing_State',
    'Billing_Street': 'Billing_Street',
    # 'box__Box_Folder_ID': 'Box_Folder_ID', #######################
    # 'Box_Folder_URL': 'Box_Folder_URL', ##########################
    'Business_Structure': 'Business_Structure',
    # 'Can_Provide_Transport': '',
    'Client_Code': 'Client_Code',
    # 'Company_Account': '',
    'Company_Email': 'Email',
    # 'Company_Type': '',
    'County': 'County',
    # 'Created_By': 'Created_By',  ###########################
    'Additional_References': 'Reference_Links',
    # 'Reference_1_Link': '',
    # 'Reference_2_Link': '',
    # 'Credit_Reference_3_Link': '',
    # 'Cultivars_of_Interest': 'Cultivars',
    # 'Curator': '',
    'Currency': 'Currency',
    'Dama_Approved': 'Dama_Approved',
    'Default_Licenses_for_Transactions_for_Books': 'Default_License_for_Transactions_in_Books',
    # 'Delivery_Windows': '',
    # 'Digital_Score_Act': '',
    'Do_you_have_a_bank_account': 'Do_you_have_a_bank_account',
    'Driver_s_Name': 'Driver_s_Name',
    'Drivers_License_Number': 'Drivers_License_Number',
    'EIN': 'EIN',
    'Employees': 'Number_of_Employees',
    'Ethics_Certifications': 'Special_Certifications',

    'Exchange_Rate': 'Exchange_Rate',
    'Facebook': 'Facebook',
    'Gate_Code': 'Gate_Code',
    'Instagram': 'Instagram',
    # 'License_2': '',
    'License_Plate_Number': 'License_Plate_Number',
    'Licenses': 'Licenses',
    'LinkedIn': 'LinkedIn',
    # 'Loading_Dock_Location': '',
    'Round_Trip_Mileage_from_Todd_Rd': 'Round_Trip_Mileage_from_Todd_Rd',
    # 'Modified_By': 'Modified_By', #########################
    # 'Ownership': '',
    # 'Owner': 'Owner', ###########################
    'Phone': 'Phone',
    'Preferred_Payment_Method': 'Preferred_Payment_Method',
    # 'Account_Contacts': '',
    # 'Product': '',
    'Region': 'Region',
    'Seller_s_Permit_Box_Link': 'Sellers_Permit_Box_Link',
    'Seller_s_Permit_Expiration_Date': 'Sellers_Permit_Expiration_Date',
    'Shipping_City': 'Shipping_City',
    'Shipping_Code': 'Shipping_Zip_Code',
    'Shipping_Country': 'Shipping_Country',
    # 'Shipping_Remarks': '',
    'Shipping_State': 'Shipping_State',
    'Shipping_Street': 'Shipping_Street',
    'SSN': 'SSN',
    'Transportation_Method': 'Transportation_Method',
    'Twitter': 'Twitter',
    # 'Show_Internal_Use_Only_Fields': '',
    'Vehicle_Make_Model': 'Vehicle_Make_Model',
    # 'Verified_License_with_State_Agency': '',
    'Website': 'Website',
}

def get_vendor_associations(vendor_id=None):
    final_response = {
        'Orgs': [],
        'Brands': [],
        'Licenses': [],
        'Contacts': [],
        'Cultivars': [],
    }

    if vendor_id:
        org = search_query('Orgs_X_Vendors', vendor_id, 'Vendor')
        if org.get('status_code') == 200:
            for o in org.get('response'):
                r = dict()
                r['name'] = o['Org']['name']
                r['id'] = o['Org']['id']
                final_response['Orgs'].append(r)

        brand = search_query('Brands_X_Vendors', vendor_id, 'Vendor')
        if brand.get('status_code') == 200:
            for b in brand.get('response'):
                r = dict()
                r['name'] = b['Brand']['name']
                r['id'] = b['Brand']['id']
                final_response['Brands'].append(r)

        license = search_query('Vendors_X_Licenses', vendor_id, 'Licenses_Module')
        if license.get('status_code') == 200:
            for l in license.get('response'):
                r = dict()
                r['name'] = l['Licenses']['name']
                r['id'] = l['Licenses']['id']
                final_response['Licenses'].append(r)

        contact = search_query('Vendors_X_Contacts', vendor_id, 'Vendor')
        if contact.get('status_code') == 200:
            for ct in contact.get('response'):
                r = dict()
                r['name'] = ct['Contact']['name']
                r['id'] = ct['Contact']['id']
                final_response['Contacts'].append(r)

        cultivar = search_query('Vendors_X_Cultivars', vendor_id, 'Cultivar_Associations')
        final_response['cultivar'] = []
        if cultivar.get('status_code') == 200:
            for cl in cultivar.get('response'):
                r = dict()
                r['name'] = cl['Cultivars']['name']
                r['id'] = cl['Cultivars']['id']
                final_response['Cultivars'].append(r)
    return final_response



def get_account_associations(account_id=None):
    final_response = {
        'Orgs': [],
        'Brands': [],
        'Licenses': [],
        'Contacts': [],
    }
    if account_id:
        org = search_query('Orgs_X_Accounts', account_id, 'Account')
        if org.get('status_code') == 200:
            for o in org.get('response'):
                r = dict()
                r['name'] = o['Org']['name']
                r['id'] = o['Org']['id']
                final_response['Orgs'].append(r)

        brand = search_query('Brands_X_Accounts', account_id, 'Account')
        if brand.get('status_code') == 200:
            for b in brand.get('response'):
                r = dict()
                r['name'] = b['Brand']['name']
                r['id'] = b['Brand']['id']
                final_response['Brands'].append(r)

        license = search_query('Accounts_X_Licenses', account_id, 'Licenses_Module')
        if license.get('status_code') == 200:
            for l in license.get('response'):
                r = dict()
                r['name'] = l['Licenses']['name']
                r['id'] = l['Licenses']['id']
                final_response['Licenses'].append(r)

        contact = search_query('Accounts_X_Contacts', account_id, 'Accounts')
        if contact.get('status_code') == 200:
            for ct in contact.get('response'):
                r = dict()
                r['name'] = ct['Contacts']['name']
                r['id'] = ct['Contacts']['id']
                final_response['Contacts'].append(r)

    return final_response


def create_duplicate_crm_vendor_from_crm_account(vendor_name,):
    f_create = False
    result = search_query('Vendors', vendor_name, 'Vendor_Name')
    if result.get('status_code') == 200:
        data_ls = result.get('response')
        if data_ls and isinstance(data_ls, list):
            vendor_name_ls = [x.get('Vendor_Name') for x in data_ls]
            if vendor_name_ls and vendor_name not in vendor_name_ls:
                f_create = True
    if result.get('status_code') == 204 or f_create:
        result = search_query('Accounts', vendor_name, 'Account_Name')
        if result.get('status_code') == 200:
            data_ls = result.get('response')
            if data_ls and isinstance(data_ls, list):
                for account in data_ls:
                    if account.get('Account_Name') == vendor_name:
                        print(f'Creating Vendor profile \'{vendor_name}\' from Account in Zoho CRM')
                        crm_obj = get_crm_obj()
                        request = list()
                        account_id = account.get('id')
                        account_record = crm_obj.get_full_record('Accounts', account_id ,)
                        if account_record['status_code'] == 200:
                            account = account_record['response']
                        data = dict()
                        for k,v in accounts_to_vendors_dict.items():
                            if account.get(k):
                                data[v] = account.get(k)
                        request.append(data)
                        resp_vendor = crm_obj.insert_records('Vendors', request,)
                        if resp_vendor.get('status_code') == 201:
                            try:
                                vendor_id = resp_vendor['response']['data'][0]['details']['id']
                            except TypeError:
                                vendor_id = resp_vendor['response'][0]['id']
                            association_data = get_account_associations(account_id=account_id)
                            if association_data['Orgs']:
                                association_data['Orgs'] = [{'Vendor': vendor_id, 'Org': x['id']} for x in association_data['Orgs']]
                                r = create_records('Orgs_X_Vendors', association_data['Orgs'])
                                if r.get('status_code') != 201:
                                    print(r)
                            if association_data['Brands']:
                                association_data['Brands'] = [{'Vendor': vendor_id, 'Brand': x['id']} for x in association_data['Brands']]
                                r = create_records('Brands_X_Vendors', association_data['Brands'])
                                if r.get('status_code') != 201:
                                    print(r)
                            if association_data['Licenses']:
                                association_data['Licenses'] = [{'Licenses_Module': vendor_id, 'Licenses': x['id']} for x in association_data['Licenses']]
                                r = create_records('Vendors_X_Licenses', association_data['Licenses'])
                                if r.get('status_code') != 201:
                                    print(r)
                            if association_data['Contacts']:
                                association_data['Contacts'] = [{'Vendor': vendor_id, 'Contact': x['id']} for x in association_data['Contacts']]
                                r = create_records('Vendors_X_Contacts', association_data['Contacts'])
                                if r.get('status_code') != 201:
                                    print(r)
                        return resp_vendor
        else:
            return result


def get_custom_inventory_data_from_crm_vendor(obj):
    if obj.vendor_name:
        try:
            result = search_query('Vendors', obj.vendor_name, 'Vendor_Name')
        except Exception:
            pass
        else:
            if result.get('status_code') == 200:
                data_ls = result.get('response')
                if data_ls and isinstance(data_ls, list):
                    for vendor in data_ls:
                        if vendor.get('Vendor_Name') == obj.vendor_name:
                            if not obj.procurement_rep:
                                p_rep = vendor.get('Owner', {}).get('email')
                                if p_rep:
                                    obj.procurement_rep = p_rep
                            client_code = vendor.get('Client_Code')
                            if client_code:
                                obj.client_code = client_code

def get_custom_inventory_data_from_crm_account(obj):
    if obj.vendor_name:
        try:
            result = search_query('Accounts', obj.vendor_name, 'Account_Name')
        except Exception:
            pass
        else:
            if result.get('status_code') == 200:
                data_ls = result.get('response')
                if data_ls and isinstance(data_ls, list):
                    for vendor in data_ls:
                        if vendor.get('Account_Name') == obj.vendor_name:
                            if not obj.procurement_rep:
                                p_rep = vendor.get('Owner', {}).get('email')
                                if p_rep:
                                    obj.procurement_rep = p_rep
                            client_code = vendor.get('Client_Code')
                            if client_code:
                                obj.client_code = client_code
