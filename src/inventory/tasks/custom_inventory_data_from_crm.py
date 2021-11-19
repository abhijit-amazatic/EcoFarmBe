from django.contrib import messages

from core.celery import (
    app,
)
from integration.crm import (
    search_query,
    get_vendor_by_clint_id,
)

from ..models import (
    CustomInventory,
)


def get_custom_inventory_data_from_crm_vendor(obj, request=None):
    # msg_error = lambda msg: messages.error(request, msg) if request else print(msg)
    msg_warning = lambda msg: messages.warning(request, msg) if request else print(msg)
    if obj.license_profile:
        client_id = obj.license_profile.license.client_id
        vendor = get_vendor_by_clint_id(client_id)
        if vendor:
            if vendor.get("id"):
                obj.crm_vendor_id = vendor.get("id")
            p_rep = vendor.get("Owner", {}).get("email")
            if p_rep:
                obj.procurement_rep = p_rep
            p_rep_name = vendor.get("Owner", {}).get("name")
            if p_rep_name:
                obj.procurement_rep_name = p_rep_name
            client_code = vendor.get("Client_Code")
            if client_code:
                obj.client_code = client_code
            else:
                vendor_name = vendor.get("Vendor_Name")
                msg_warning(
                    f"client code not found for vendor '{vendor_name}' (client_id: {client_id}) in Zoho CRM"
                )
        else:
            msg_warning("Vendor not found in Zoho CRM")


@app.task(queue="general")
def get_custom_inventory_data_from_crm_task(custom_inventory_id):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    get_custom_inventory_data_from_crm_vendor(item)
    item.save()
