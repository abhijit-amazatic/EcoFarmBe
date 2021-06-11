import re
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

from fee_variable.models import (TaxVariable, )
from fee_variable.utils import (get_item_mcsp_fee,)
from integration.inventory import (
    get_inventory_obj,
    update_inventory_item,
    create_purchase_order,
    submit_purchase_order
)
from brand.models import (LicenseProfile, )
from .notify_item_change_approved import (notify_inventory_item_change_approved_task, )
from  ..data import (CATEGORY_GROUP_MAP)

CG = {cat: k for k, v in CATEGORY_GROUP_MAP.items() for cat in v}

def get_approved_by(request=None):
    approved_by = {
        'email': 'connect@thrive-society.com',
        'phone': '',
        'name': 'Automated Bot',
    }
    if request:
        approved_by = {
            'email': request.user.email,
            'phone': request.user.phone.as_e164,
            'name': request.user.get_full_name(),
        }
    return approved_by


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


def inventory_item_change(obj, request=None):
    if obj.status == 'pending_for_approval':
        mcsp_fee = get_item_mcsp_fee(
            obj.vendor_name,
            license_profile=obj.license_profile,
            item_category_group=CG.get(obj.category_name),
            request=request,
        )
        if mcsp_fee:
            tax = get_item_tax(obj, request)
            if tax:
                data = obj.get_item_update_data()
                if obj.farm_price:
                    data['price'] = obj.farm_price + mcsp_fee + tax
                    data['rate'] = obj.farm_price + mcsp_fee + tax
                inventory_org = data.get('inventory_name', '').lower()
                if inventory_org in ('efd', 'efn', 'efl'):
                    inventory_name = 'inventory_{inventory_org}'
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
                            obj.approved_by = get_approved_by(request=request)
                            obj.save()
                            if request:
                                messages.success(request, 'This change is approved and updated in Zoho Inventory')
                            notify_inventory_item_change_approved_task.delay(obj.id)
                        else:
                            if request:
                                messages.error(request, 'Error while updating item in Zoho Inventory')
                            print('Error while updating item in Zoho Inventory')
                            print(result)
                            print(data)
                else:
                    if request:
                        messages.error(request, 'Item have invalid inventory name.')
                    print('Item have invalid inventory name.')



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
    inv_obj = get_inventory_obj(inventory_name='inventory_efd',)
    po_obj = inv_obj.PurchaseOrders()
    # pr_obj = inv_obj.PurchaseReceives()
    po = get_po_for_item_quantity_change(obj, request, po_obj=po_obj)
    if po:
        po_id = po.get('purchaseorder_id')
        line_items = [ x for x in po.get('line_items') if x.get('item_id') != item_id]
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
                    obj.approved_by = get_approved_by(request=request)
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
        result = create_custom_inventory_item_po(
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
            obj.approved_by = get_approved_by(request=request)
            obj.save()
            submit_purchase_order(obj.po_id)


def get_tax_from_db(tax='flower', request=None):
    try:
        tax_var = TaxVariable.objects.latest('-created_on')
    except TaxVariable.DoesNotExist:
        pass
    else:
        if tax=='flower':
            tax='cultivar_tax'
        elif tax=='trim':
            tax='trim_tax'
        else:
            tax = None
        if tax:
            try:
                return float(getattr(tax_var, tax))
            except ValueError:
                return None


def get_item_tax(obj, request=None):
    msg_error = lambda msg: messages.error(request, msg,) if request else None
    # CG = CATEGORY_GROUP_MAP
    if obj.category_name:
        if CG.get(obj.category_name, '')  == 'Flowers':
            tax = get_tax_from_db(tax='flower')
            if isinstance(tax, float):
                return tax
        if CG.get(obj.category_name, '') == 'Trims':
            tax = get_tax_from_db(tax='trim')
            if isinstance(tax, float):
                return tax
        if CG.get(obj.category_name, '') in ('Isolates', 'Concentrates', 'Terpenes'):
            trim_tax = get_tax_from_db(tax='trim')
            if isinstance(trim_tax, float):
                if obj.trim_used:
                    return (trim_tax * obj.trim_used) / obj.quantity_available
                else:
                    msg_error('Not provided quantity of Trim used to produce the oil.')
                    return None
        if CG.get(obj.category_name, '') == 'Clones':
            return float(0.0)
        else:
            msg_error('No Cultivar Tax is defined for selected category.')
            return None

    msg_error('No Cultivar Tax found.')
    return None
