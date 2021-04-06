import re
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

from fee_variable.utils import (get_tax_and_mcsp_fee,)
from integration.crm import (get_crm_obj, search_query, create_records)
from integration.inventory import (get_inventory_obj, update_inventory_item,)
from integration.books import (create_purchase_order, submit_purchase_order)
from brand.models import (LicenseProfile, )


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
                            if not obj.crm_vendor_id:
                                obj.crm_vendor_id = vendor.get('id')
                            if not obj.procurement_rep:
                                p_rep = vendor.get('Owner', {}).get('email')
                                if p_rep:
                                    obj.procurement_rep = p_rep
                                p_rep_name = vendor.get('Owner', {}).get('name')
                                if p_rep_name:
                                    obj.procurement_rep_name = p_rep_name
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
                                p_rep_name = vendor.get('Owner', {}).get('name')
                                if p_rep_name:
                                    obj.procurement_rep_name = p_rep_name
                            client_code = vendor.get('Client_Code')
                            if client_code:
                                obj.client_code = client_code

def create_po(sku, quantity, vendor_name, client_code):
    try:
        lp_obj = LicenseProfile.objects.get(name=vendor_name)
    except Exception:
        license_number = ''
    else:
        license_number = lp_obj.license.license_number
    warehouse_id = None
    inv_obj = get_inventory_obj(inventory_name='inventory_efd',)
    result = inv_obj.list_warehouses()
    if result.get('code') == 0:
        warehouses = result.get("warehouses", [])
        warehouses = [
            warehouse
            for warehouse in warehouses
            if warehouse.get('warehouse_name', '').strip() == getattr(settings, 'CUSTOM_INVENTORY_WAREHOUSE_NAME', '').strip()
        ]
        if warehouses:
            warehouse_id = warehouses[0].get('warehouse_id')
    item_data = {
        "sku": sku,
        "quantity": int(quantity),
        "rate": 0.0,
        "reference_number": "To feed the CFI",
    }
    if warehouse_id:
        item_data['warehouse_id'] = warehouse_id
    data = {
        'vendor_name': vendor_name,
        "line_items": [item_data],
        "custom_fields": [
            {
                "api_name": "cf_client_code",
                "value": client_code,
            },
            {
                "api_name": "cf_billing_published",
                "value": True,
            },
        ],
    }
    if license_number:
        data['custom_fields'].append({
            "api_name": "cf_client_license",
            "value": license_number,
        })
    # if procurement_rep_id:
    #     data['custom_fields'].append({
    #         "api_name": "cf_procurement_rep",
    #         "value": "",
    #     })
    return create_purchase_order(data, params={})



def inventory_item_change(obj, request=None):
    if obj.status == 'pending_for_approval':
        tax_and_mcsp_fee = get_tax_and_mcsp_fee(obj.item.cf_vendor_name, request)
        if tax_and_mcsp_fee:
            data = obj.get_item_update_data()
            if obj.farm_price:
                data['price'] = obj.farm_price + sum(tax_and_mcsp_fee)
                data['rate'] = obj.farm_price + sum(tax_and_mcsp_fee)
            inventory_name = 'inventory_efd' if data.get('inventory_name') == 'EFD' else 'inventory_efl'
            data.pop('inventory_name')
            try:
                result = update_inventory_item(inventory_name, data.get('item_id'), data)
            except Exception as exc:
                if request:
                    messages.error(request, 'Error while updating item in Zoho Inventory',)
                print('Error while updating item in Zoho Inventory')
                print(exc)
                print(data)
            else:
                if result.get('code') == 0:
                    obj.status = 'approved'
                    obj.approved_on = timezone.now()
                    if request:
                        obj.approved_by = {
                            'email': request.user.email,
                            'phone': request.user.phone.as_e164,
                            'name': request.user.get_full_name(),
                        }
                    else:
                        obj.approved_by = {
                            'email': 'connect@thrive-society.com',
                            'phone': '',
                            'name': 'Automated Bot',
                        }
                    obj.save()
                    if request:
                        messages.success(request, 'This change is approved and updated in Zoho Inventory')
                    # create_approved_item_po.apply_async((obj.id,), countdown=5)
                    # notify_inventory_item_approved.delay(obj.id)
                else:
                    if request:
                        messages.error(request, 'Error while updating item in Zoho Inventory')
                    print('Error while updating item in Zoho Inventory')
                    print(result)
                    print(data)


def get_po_for_item_quantity_change(obj, request=None, po_obj=None):
    if not po_obj:
        inv_obj = get_inventory_obj(inventory_name='inventory_efd',)
        po_obj = inv_obj.PurchaseOrders()
    try:
        result = po_obj.list_purchase_orders(parameters={'item_id': obj.item.item_id}, parse=False)
    except Exception as exc:
        if request:
            messages.error(request, 'Error while geting item Purchase Order from Zoho Books',)
        print('Error while geting item Purchase Order from Zoho Books')
        print(exc)
    else:
        if result.get('code') == 0:
            po_ls = result.get('purchaseorders')
            if po_ls:
                for _po in po_ls:
                    po_ref = _po.get('reference_number', '')
                    po_ref_condensed = re.sub(r"[\W\s]", '', po_ref)
                    if po_ref_condensed.lower() == 'tofeedthecfi':
                        po_id = _po.get('purchaseorder_id')
                        po_result = po_obj.get_purchase_order(po_id=po_id, parameters={}, parse=False)
                        if po_result.get('code') == 0:
                            po = po_result.get('purchaseorder', {})
                            if po:
                                # if po.get('bills'):
                                #     for bill in po.get('bills'):
                                #         bill_res = bill_obj.delete_bill(bill_id=bill.get('bill_id'))
                                #         if bill_res.get('code') != 0:
                                #             if request:
                                #                 messages.error(request, 'Purchase Order not found for this item.')
                                #             print('Error while deleting PO bill.')
                                #             print(bill_res)
                                return po
            if request:
                messages.error(request, 'Purchase Order not found for this item.')
            print('Purchase Order not found for the item.')


def add_item_quantity(obj, request=None):
    if request:
        approved_by = {
            'email': request.user.email,
            'phone': request.user.phone.as_e164,
            'name': request.user.get_full_name(),
        }
    else:
        approved_by = {
            'email': 'connect@thrive-society.com',
            'phone': '',
            'name': 'Automated Bot',
        }

    item_id = obj.item.item_id
    inv_obj = get_inventory_obj(inventory_name='inventory_efd',)
    po_obj = inv_obj.PurchaseOrders()
    # pr_obj = inv_obj.PurchaseReceives()
    po = get_po_for_item_quantity_change(obj, request, po_obj=po_obj)
    if po:
        po_id = po.get('purchaseorder_id')
        line_items = [ x for x in po.get('line_items') if x.get('item_id') != item_id]
        for item in po.get('line_items'):
            if item.get('item_id') == item_id:
                item['quantity'] += int(obj.quantity)
                line_items.append(item)
                update_result = po_obj.update_purchase_order(po_id, {'line_items': line_items}, parameters={})
                if update_result.get('code') == 0:
                    # pr_data = {
                    #     'line_items': [
                    #         {k:v for k, v in item.items() if k in ['line_item_id', 'quantity',]}
                    #         for item in line_items
                    #     ],
                    #     'date': timezone.now().strftime("%Y-%m-%d"),
                    # }
                    # pr_res = pr_obj.create_purchase_receive(pr_data, parameters={'purchaseorder_id': po_id})
                    # print(pr_res)
                    obj.status = 'approved'
                    obj.approved_by = approved_by
                    obj.approved_on = timezone.now()
                    obj.save()
                    if request:
                        messages.success(request, 'This change is approved and updated in Zoho Inventory')
                    return True
                else:
                    if request:
                        messages.error(request, update_result.get('message'))
                    print(update_result)
                    return False
    else:
        result = create_po(
            sku=obj.item.sku,
            quantity=obj.quantity,
            vendor_name=obj.item.cf_vendor_name,
            client_code=obj.item.cf_client_code
        )
        if result.get('code') == 0:
            obj.po_id = result.get('purchaseorder', {}).get('purchaseorder_id')
            obj.po_number = result.get('purchaseorder', {}).get('purchaseorder_number')
            obj.status = 'approved'
            obj.approved_on = timezone.now()
            obj.approved_by = approved_by
            obj.save()
            submit_purchase_order(obj.po_id)


