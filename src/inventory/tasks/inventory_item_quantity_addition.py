import re
from django.utils import timezone
from django.contrib import messages

from core.celery import (app,)
from integration.inventory import (
    get_inventory_obj,
    submit_purchase_order
)
from utils import (get_approved_by, )
from brand.models import (
    LicenseProfile,
)
from ..models import (
    InventoryItemQuantityAddition,
)

from .create_approved_item_po import (create_custom_inventory_item_po, )


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
                            po = po_result.get('purchaseorder')
                            if po:
                                return po
            if request:
                messages.error(request, 'Purchase Order not found for this item.')
            print('Purchase Order not found for the item.')


def add_item_quantity(obj, request=None):
    item_id = obj.item.item_id
    inventory_org = obj.inventory_name.lower()
    inv_obj = get_inventory_obj(inventory_name=f'inventory_{inventory_org}',)
    po_obj = inv_obj.PurchaseOrders()
    # pr_obj = inv_obj.PurchaseReceives()
    po = get_po_for_item_quantity_change(obj, request, po_obj=po_obj)
    if po:
        po_id = po.get('purchaseorder_id')
        line_items = [x for x in po.get('line_items') if x.get('item_id') != item_id]
        for item in po.get('line_items'):
            if item.get('item_id') == item_id:
                item['quantity'] += obj.quantity
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
                    obj.approved_by = get_approved_by(user=request.user)
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
        try:
            lp = LicenseProfile.objects.get(name=obj.item.cf_vendor_name)
        except LicenseProfile.DoesNotExist:
            print(f"License Profile '{obj.item.cf_vendor_name}' not found")
        else:
            result = create_custom_inventory_item_po(
                inventory_name=inventory_org,
                sku=obj.item.sku,
                quantity=obj.quantity,
                license_profile=lp,
                client_code=obj.item.cf_client_code,
            )
            if result.get('code') == 0:
                obj.po_id = result.get('purchaseorder', {}).get('purchaseorder_id')
                obj.po_number = result.get('purchaseorder', {}).get('purchaseorder_number')
                obj.status = 'approved'
                obj.approved_on = timezone.now()
                obj.approved_by = get_approved_by(user=request.user)
                obj.save()
                submit_purchase_order(inventory_name=f'inventory_{inventory_org}', po_id=obj.po_id)

@app.task(queue="general")
def inventory_item_quantity_addition_task(item_quantity_addition_id):
    obj = InventoryItemQuantityAddition.objects.get(id=item_quantity_addition_id)
    add_item_quantity(obj)
