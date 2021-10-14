
from core.celery import (app, )
from integration.crm import (search_query, )

from ..models import (
    CustomInventory,
)



def get_custom_inventory_data_from_crm_vendor(obj):
    if obj.license_profile:
        client_id = obj.license_profile.license.client_id
        try:
            result = search_query('Vendors', client_id, 'Client_ID')
        except Exception:
            pass
        else:
            if result.get('status_code') == 200:
                data_ls = result.get('response')
                if data_ls and isinstance(data_ls, list):
                    for vendor in data_ls:
                        if vendor.get('Client_ID') == client_id:
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

# def get_custom_inventory_data_from_crm_account(obj):
#     if obj.vendor_name:
#         try:
#             result = search_query('Accounts', obj.vendor_name, 'Account_Name')
#         except Exception:
#             pass
#         else:
#             if result.get('status_code') == 200:
#                 data_ls = result.get('response')
#                 if data_ls and isinstance(data_ls, list):
#                     for vendor in data_ls:
#                         if vendor.get('Account_Name') == obj.vendor_name:
#                             if not obj.procurement_rep:
#                                 p_rep = vendor.get('Owner', {}).get('email')
#                                 if p_rep:
#                                     obj.procurement_rep = p_rep
#                                 p_rep_name = vendor.get('Owner', {}).get('name')
#                                 if p_rep_name:
#                                     obj.procurement_rep_name = p_rep_name
#                             client_code = vendor.get('Client_Code')
#                             if client_code:
#                                 obj.client_code = client_code

@app.task(queue="general")
def get_custom_inventory_data_from_crm_task(custom_inventory_id):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    get_custom_inventory_data_from_crm_vendor(item)
    # if not item.client_code:
    #     get_custom_inventory_data_from_crm_account(item)
    item.save()
