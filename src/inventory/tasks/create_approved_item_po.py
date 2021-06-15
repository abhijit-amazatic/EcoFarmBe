from django.conf import settings

from core.celery import (app,)
from integration.inventory import (
    get_inventory_obj,
    create_purchase_order,
    submit_purchase_order
)
from brand.models import (LicenseProfile, )
from ..models import (
    CustomInventory,
)



def create_custom_inventory_item_po(inventory_name, sku, quantity, vendor_name, client_code):
    # inventory_name = f'inventory_{custom_inventory_zoho_org}'
    # books_name = f'books_{custom_inventory_zoho_org}'
    try:
        lp_obj = LicenseProfile.objects.get(name=vendor_name)
    except Exception:
        license_number = ''
    else:
        license_number = lp_obj.license.license_number
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
        'vendor_name': vendor_name,
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
            inventory_name=inventory_name,
            sku=item.sku,
            quantity=item.quantity_available,
            vendor_name=item.vendor_name,
            client_code=item.client_code
        )
        if result.get('code') == 0:
            item.po_id = result.get('purchaseorder', {}).get('purchaseorder_id')
            item.po_number = result.get('purchaseorder', {}).get('purchaseorder_number')
            item.save()
            submit_purchase_order(inventory_name=inventory_name, po_id=item.po_id)

