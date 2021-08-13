import traceback
import copy

from django.conf import settings
from django.contrib.auth import get_user_model

from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail_send,)
from utils import (reverse_admin_change_path,)

from ..models import (
    CustomInventory,
)

slack = Slacker(settings.SLACK_TOKEN)
User = get_user_model()


def notify_slack_inventory_item_approved(data):
    """
    as new Inventory item approved, inform admin on slack.
    """
    details = "".join([f"- *{v[0]}:* {v[1]} \n" for v in data.get('details_display', [])])
    links = "".join([f"- *{v[0]}:* {v[1]} \n" for v in data.get('links_display', [])])
    msg = (
        f"<!channel> Inventory item *{data.get('item_name')}* is approved by *{data.get('approved_by_name')}* (User ID: `{data.get('approved_by_email')}`).\n\n"
        f"Item details are as follows!\n"
        f"{details}"
        f"\n\n"
        f"{links}"
        f"\n"
    )

    slack.chat.post_message(settings.SLACK_INVENTORY_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_email_inventory_item_approved(data):
    """
    as new Inventory item approved, send notification mail.
    """
    if data.get('created_by_email'):
        try:
            mail_send(
                "email/notification_inventory_item_approved.html",
                data,
                "Inventory Item Approved",
                data.get('created_by_email'),
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)

def notify_logistics_slack_inventory_item_approved(data):
    """
    as new Inventory item approved, inform Logistic on slack.
    """
    details = "".join([f"- *{v[0]}:* {v[1]} \n" for v in data.get('details_display', [])])
    links = "".join([f"- *{v[0]}:* {v[1]} \n" for v in data.get('links_display', [])])
    msg = (
        f"<!channel> New Inventory item is added. Logistics detail summary for the item is as follows:\n"
        f"{details}"
        f"\n\n"
        f"{links}"
        f"\n"
    )
    slack.chat.post_message(settings.SLACK_LOGISTICS_TRANSPORT_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_logistics_email_inventory_item_approved(data):
    """
    as new Inventory item approved, send Logistic notification mail.
    """
    if data.get('created_by_email'):
        try:
            mail_send(
                "email/notification_inventory_item_approved_logistics.html",
                data,
                "New Inventory Item",
                settings.NOTIFICATION_EMAIL_LOGISTICS_TRANSPORT,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_approved_task(custom_inventory_id, notify_logistics=True):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        if obj.status == 'approved':
            # data = copy.deepcopy(obj.__dict__)
            data = dict()
            data['item_name'] = obj.cultivar.cultivar_name
            data['approved_by_email'] = obj.approved_by.get('email')
            data['approved_by_name'] = obj.approved_by.get('name')
            data['created_by_email'] = obj.created_by.get('email')
            data['created_by_name'] = obj.created_by.get('name')



            data['details_display'] = {
                'Vendor Name':             obj.vendor_name,
                'Client Code':             obj.client_code,
                'Product Category':        obj.category_name,
                'Cultivar Name':           obj.cultivar.cultivar_name,
                'Cultivar Type':           obj.cultivar.cultivar_type,
                'SKU':                     obj.sku,
                'Marketplace Status':      obj.marketplace_status,
                'Quantity':                obj.quantity_available,
                'Farm Price':              "${:,.2f}".format(obj.farm_ask_price) if obj.farm_ask_price else '',
                'Pricing Position':        obj.pricing_position,
                # 'Min Qty Purchase':        obj.minimum_order_quantity,
                'Seller Grade Estimate':   obj.grade_estimate,
                'Need Testing':            'Yes' if data.get('need_lab_testing_service') else 'No',
                'Batch Availability Date': obj.batch_availability_date,
                'Harvest Date':            obj.harvest_date,
                'Batch Quality Notes':     obj.product_quality_notes,
                'Procurement Rep':         obj.procurement_rep_name,
            }.items()

            data['links_display'] = {
                'Admin Link':               f'https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}',
                'Zoho Inventory Item Link': f'https://inventory.zoho.com/app#/inventory/items/{obj.zoho_item_id}',
                # 'Webapp Item Link':         f'{settings.FRONTEND_DOMAIN_NAME.rstrip("/")}/marketplace/{obj.zoho_item_id}/item/',
                # 'CRM Vendor Link':          f'{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Vendors/{obj.crm_vendor_id}' if obj.crm_vendor_id else '',
            }.items()


            notify_slack_inventory_item_approved(data)
            notify_email_inventory_item_approved(data)
            if notify_logistics:
                if obj.transportation:
                    pick_time = []
                    if obj.best_contact_time_from:
                        pick_time.append(obj.best_contact_time_from.strftime("%I:%M %p"))
                    if obj.best_contact_time_to:
                        pick_time.append(obj.best_contact_time_to.strftime("%I:%M %p"))

                    pickup = []
                    if obj.best_contact_Day_of_week:
                        pickup.append(obj.best_contact_Day_of_week.title())
                    if pick_time:
                        pickup.append(' - '.join(pick_time))

                    data['details_display'] = {
                        'Transportation / Sample Pickup':          obj.transportation,
                        'Best time to call to arrange for pickup': ' '.join(pickup),
                        'Vendor Name':                             obj.vendor_name,
                        'Client Code':                             obj.client_code,
                        'Product Category':                        obj.category_name,
                        'Cultivar Name':                           obj.cultivar.cultivar_name,
                        'Quantity Available':                      obj.quantity_available,
                    }.items()

                    data['links_display'] = {
                        'Admin Link':      f'https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}',
                        'CRM Vendor Link': f'{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Vendors/{obj.crm_vendor_id}' if obj.crm_vendor_id else '',
                    }.items()

                    notify_logistics_slack_inventory_item_approved(data)
                    notify_logistics_email_inventory_item_approved(data)

