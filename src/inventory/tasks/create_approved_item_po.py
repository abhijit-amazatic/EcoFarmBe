from django.conf import settings

from core.celery import (app,)
from integration.inventory import (
    get_inventory_obj,
    create_purchase_order,
    submit_purchase_order
)
from integration.crm import (
    search_query,
)
from integration.books import (
    get_books_obj,
)
from brand.models import (LicenseProfile, )
from ..models import (
    CustomInventory,
    Vendor,
)

def get_vendor_id(license_profile, zoho_organization):
    contact_id = None
    contact_ids = license_profile.license.zoho_books_vendor_ids
    if contact_ids.get(zoho_organization):
        contact_id = contact_ids.get(zoho_organization).strip()
    if not contact_id:
        crm_profile_id = license_profile.zoho_crm_vendor_id
        if not crm_profile_id:
            r = search_query('Vendors', license_profile.license.client_id, 'Client_ID')
            if r['status_code'] == 200:
                for crm_profile in r['response']:
                    if crm_profile['Client_ID'] == license_profile.license.client_id:
                        crm_profile_id = crm_profile['id']
                        break

        books_obj = get_books_obj(f'books_{zoho_organization}')
        contact_obj = books_obj.Contacts()
        r = contact_obj.get_contact_using_crm_account_id(crm_profile_id)
        try:
            if r and r.get('code') == 0:
                for c in r.get('contacts', []):
                    if c.get('contact_type') == 'vendor':
                        if c.get('contact_id'):
                            contact_id = c.get('contact_id')
        except Exception as e:
            print(e)
    return contact_id




def create_custom_inventory_item_po(zoho_organization, sku, quantity, license_profile, client_code):
    inventory_name = f'inventory_{zoho_organization}'
    # books_name = f'books_{custom_inventory_zoho_org}'
    license_number = license_profile.license.license_number
    warehouse_id = None
    inv_obj = get_inventory_obj(inventory_name=inventory_name,)
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
    }
    if warehouse_id:
        item_data['warehouse_id'] = warehouse_id
    data = {
        "reference_number": "To feed the CFI",
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
    vendor_id = get_vendor_id(license_profile, zoho_organization)
    if vendor_id:
        data["vendor_id"] = vendor_id
    else:
        data["vendor_name"] = license_profile.name

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
    return create_purchase_order(inventory_name=inventory_name, record=data, params={})


@app.task(queue="general")
def create_approved_item_po_task(custom_inventory_id):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    if item.status == 'approved':
        inventory_name = f'inventory_{item.zoho_organization}'
        result = create_custom_inventory_item_po(
            zoho_organization=item.zoho_organization,
            sku=item.sku,
            quantity=item.quantity_available,
            license_profile=item.license_profile,
            client_code=item.client_code
        )
        if result.get('code') == 0:
            item.po_id = result.get('purchaseorder', {}).get('purchaseorder_id')
            item.po_number = result.get('purchaseorder', {}).get('purchaseorder_number')
            item.save()
            submit_purchase_order(inventory_name=inventory_name, po_id=item.po_id)

