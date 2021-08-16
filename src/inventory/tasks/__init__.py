
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

from .export_csv import (
    county_update_create,
    save_daily_aggrigated_summary,
    save_daily_aggrigated_county_summary,
    export_inventory_csv,
    export_inventory_aggrigated_csv,
    export_inventory_aggrigated_county_csv,
)
from integration.inventory import update_inventory_item
from .notify_item_submitted import (notify_inventory_item_submitted_task, )
from .notify_item_approved import (notify_inventory_item_approved_task, )
from .notify_item_change_submitted import (notify_inventory_item_change_submitted_task, )
from .notify_item_change_approved import (notify_inventory_item_change_approved_task, )
from .notify_item_delist_submitted import (notify_inventory_item_delist_submitted_task,)
from .notify_item_delist_approved import (notify_inventory_item_delist_approved_task,)
from .crm_vendor_from_crm_account import (create_duplicate_crm_vendor_from_crm_account_task, )
from .custom_inventory_data_from_crm import (get_custom_inventory_data_from_crm_task, )
from .create_approved_item_po import (create_approved_item_po_task, )
from .inventory_item_quantity_addition import (inventory_item_quantity_addition_task, )


@app.task(queue="urgent", serializer='json')
def async_update_inventory_item(inventory_name,item_id,item):
    """
    async task for insert inventory items.
    """
    update_inventory = update_inventory_item(inventory_name,item_id,item)
    return {"Task Processed": True} 


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

