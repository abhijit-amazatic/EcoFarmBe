
"""
All tasks related to inventory. 
"""
import traceback
import copy
from django.conf import settings

from celery.task import periodic_task
from celery.schedules import crontab
from slacker import Slacker

from core.celery import app
from core.mailer import mail, mail_send

from .models import (CustomInventory, )

slack = Slacker(settings.SLACK_TOKEN)

def notify_slack_inventory_item_added(data):
    """
    as new Inventory item added, inform admin on slack.
    """
    msg = (f"<!channel>New Inventory item is Submitted by user associated with the EmailID `{data.get('user_email')}`. Please review and approve the item!\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Cultivar Type:* {data.get('cultivar_type')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Price:* {data.get('farm_ask_price')}\n"
        f"- *Pricing Position:* {data.get('pricing_position')}\n"
        f"- *Min Qty Purchase:* {data.get('minimum_order_quantity')}\n"
        f"- *Harvest Date:* {data.get('harvest_date')}\n"
        f"- *Lab Test Yes / No:* {data.get('need_lab_testing_service')}\n"
        f"- *Batch Availability Date:* {data.get('batch_availability_date')}\n"
        f"- *Grade Estimate:* {data.get('grade_estimate')}\n"
        f"- *Batch Quality Notes:* {data.get('product_quality_notes')}\n"
    )
    slack.chat.post_message(settings.SLACK_SALES_CHANNEL, msg, as_user=True)

def notify_email_inventory_item_added(data):
    """
    as new Inventory item added, send notification mail.
    """
    try:
        mail_send(
            "inventory_item_add_notify.html",
            data,
            "New Inventory Item.",
            settings.INVENTORY_NOTIFICATION_EMAIL,
        )
    except Exception as e:
        traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_added(email, custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        data = copy.deepcopy(obj.__dict__)
        data['cultivar_name'] = obj.cultivar.cultivar_name
        data['cultivar_type'] = obj.cultivar.cultivar_type
        data['user_email'] = email
        notify_slack_inventory_item_added(data)
        notify_email_inventory_item_added(data)
