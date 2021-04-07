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
    msg = (f"<!channel>Inventory item is approved by *{data.get('approved_by_name')}* (User ID: `{data.get('approved_by_email')}`).\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"- *Client Code:* {data.get('client_code')}\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Cultivar Type:* {data.get('cultivar_type')}\n"
        f"- *SKU:* {data.get('sku')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Farm Price:* {data.get('farm_price_formated')}\n"
        f"- *Pricing Position:* {data.get('pricing_position')}\n"
        # f"- *Min Qty Purchase:* {data.get('minimum_order_quantity')}\n"
        f"- *Seller Grade Estimate:* {data.get('grade_estimate')}\n"
        f"- *Need Testing:* { 'Yes' if data.get('need_lab_testing_service') else 'No'}\n"
        f"- *Batch Availability Date:* {data.get('batch_availability_date')}\n"
        f"- *Harvest Date:* {data.get('harvest_date')}\n"
        f"- *Batch Quality Notes:* {data.get('product_quality_notes')}\n"
        f"- *Procurement Rep:* {data.get('procurement_rep_name')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
        f"- *Zoho Inventory Item Link:* {data.get('zoho_item_link')}\n"
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
    msg = (f"<!channel>New Inventory item is added. Logistics detail summary for the item is as follows:\n"
        f"- *Transportation / Sample Pickup:* {data.get('transportation')}\n"
        f"- *Best time to call to arrange for pickup:* "
        f"{data.get('best_day')} {data.get('best_time_from')} - {data.get('best_time_to')}\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"- *Client Code:* {data.get('client_code')}\n"
        f"- *Product Category:* {data.get('category_name')}\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
        f"- *CRM Vendor Link:* {data.get('crm_vendor_link')}\n"
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
def notify_inventory_item_approved_task(custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        if obj.status == 'approved':
            data = copy.deepcopy(obj.__dict__)
            data['cultivar_name'] = obj.cultivar.cultivar_name
            data['cultivar_type'] = obj.cultivar.cultivar_type
            data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
            data['approved_by_email'] = obj.approved_by.get('email')
            data['approved_by_name'] = obj.approved_by.get('name')
            data['created_by_email'] = obj.created_by.get('email')
            data['created_by_name'] = obj.created_by.get('name')
            data['zoho_item_link'] = f"https://inventory.zoho.com/app#/inventory/items/{obj.zoho_item_id}"
            data['webapp_item_link'] = f"{settings.FRONTEND_DOMAIN_NAME}/marketplace/{obj.zoho_item_id}/item/"
            if obj.farm_ask_price:
                data['farm_price_formated'] = "${:,.2f}".format(obj.farm_ask_price)
            if obj.best_contact_Day_of_week:
                data['best_day'] = obj.best_contact_Day_of_week.title()
            if obj.best_contact_time_from:
                data['best_time_from'] = obj.best_contact_time_from.strftime("%I:%M %p")
            if obj.best_contact_time_to:
                data['best_time_to'] = obj.best_contact_time_to.strftime("%I:%M %p")
            if obj.crm_vendor_id:
                data['crm_vendor_link'] = f"{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Vendors/{obj.crm_vendor_id}"
            notify_slack_inventory_item_approved(data)
            notify_logistics_slack_inventory_item_approved(data)
            notify_email_inventory_item_approved(data)
            notify_logistics_email_inventory_item_approved(data)

