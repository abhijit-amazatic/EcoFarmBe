
"""
All tasks related to inventory. 
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from celery.task import periodic_task
from celery.schedules import crontab
from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail, mail_send)

from integration.box import (upload_file, upload_file_stream, )
from integration.inventory import (
    get_inventory_obj,
    update_inventory_item,
    create_purchase_order,
    submit_purchase_order
)

from .helpers import (
    inventory_item_change,
    add_item_quantity,
    create_custom_inventory_item_po,
)
from ..models import (
    Inventory,
    CustomInventory,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
    InventoryItemEdit,
    InventoryItemQuantityAddition,
)

from .export_csv import (
    county_update_create,
    save_daily_aggrigated_summary,
    save_daily_aggrigated_county_summary,
    export_inventory_csv,
    export_inventory_aggrigated_csv,
    export_inventory_aggrigated_county_csv,
)
from .notify_item_added import (notify_inventory_item_added_task, )
from .notify_item_approved import (notify_inventory_item_approved_task, )
from .notify_item_change_submitted import (notify_inventory_item_change_submitted_task, )
from .notify_item_change_approved import (notify_inventory_item_change_approved_task, )
from .crm_vendor_from_crm_account import (create_duplicate_crm_vendor_from_crm_account_task, )
from .custom_inventory_data_from_crm import (get_custom_inventory_data_from_crm_task )



@app.task(queue="general")
def create_approved_item_po(custom_inventory_id):
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


# @app.task(queue="general")
# def inventory_item_change_task(inventory_items_change_request_id):
#     obj = InventoryItemEdit.objects.get(id=inventory_items_change_request_id)
#     # history_qs = obj.item.history.filter(cf_farm_price_2__gt=0)
#     # if history_qs:
#     #     h_obj = history_qs.earliest('history_date')
#     #     if abs(h_obj.cf_farm_price_2 - obj.farm_price) <= 50:
#     #         inventory_item_change(obj)

#     # elif obj.item.cf_farm_price_2:
#     #     if abs(obj.item.cf_farm_price_2 - obj.farm_price) <= 50:
#     #         inventory_item_change(obj)
#     # else:
#         # inventory_item_change(obj)
#     inventory_item_change(obj)

@app.task(queue="general")
def inventory_item_quantity_addition_task(item_quantity_addition_id):
    obj = InventoryItemQuantityAddition.objects.get(id=item_quantity_addition_id)
    add_item_quantity(obj)
