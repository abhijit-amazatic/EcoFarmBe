
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

from brand.models import (
    License,
)
from inventory.models import (
    InTransitOrder,
)
from integration.inventory import (
    update_inventory_item,
    sync_inventory,
)
from integration.apps.twilio import (send_sms,)
from .export_csv import (
    county_update_create,
    save_daily_aggrigated_summary,
    save_daily_aggrigated_county_summary,
    export_inventory_csv,
    export_inventory_aggrigated_csv,
    export_inventory_aggrigated_county_csv,
)

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
from .inventory_tax_update import (update_zoho_item_tax, )
from .qr_code import *

from ..models import Inventory

@app.task(queue="urgent", serializer='json')
def async_update_inventory_item(inventory_name,item_id,item):
    """
    async task for insert inventory items.
    """
    update_inventory = update_inventory_item(inventory_name,item_id,item)
    return {"Task Processed": True} 

@app.task(queue="urgent", serializer='json')
def inventory_sync_task(inventory_name, record):
    """
    inventory sync.
    """
    sync_inventory(inventory_name, record)
    try:
        obj = Inventory.objects.get(item_id=record['item_id'])
        if not obj.item_qr_code_url:
            generate_upload_item_detail_qr_code_stream.delay(obj.item_id)
    except Inventory.DoesNotExist as e:
        print(f"Error{e}")
    print(f"proccessed item_id: {record['item_id']}")


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

@periodic_task(run_every=(crontab(hour=[8], minute=0)), options={"queue": "general"})
def send_pending_cart_notification():
    cart = {profile_id: order_data
        for profile_id, order_data in InTransitOrder.objects.filter(profile_id=392).values_list('profile_id', 'order_data')
        if order_data
    }
    license_qs = License.objects.select_related('license_profile').filter(license_profile__id__in=cart.keys())
    for license_obj in license_qs:
        try:
            items = [
                item.get('name')
                for cart_org in cart[license_obj.license_profile.id].values()
                for item in cart_org.get('cart_item', [])
                if all([bool(x.lower() not in item.get('name', '').lower()) for x in ('Cultivation Tax', 'MCSP')])
            ]
        except Exception as e:
            print(e)
        else:
            url = f"{settings.FRONTEND_DOMAIN_NAME}/marketplace/order/{license_obj.client_id}"
            msg = f"Hi, you still have these {', '.join(items)} items in your cart . Would you like to complete your checkout? {url}"
            # print(msg)
            for user in license_obj.cart_notification_users.filter(receive_cart_notification=True):
                send_sms(user.phone.as_e164, msg)
