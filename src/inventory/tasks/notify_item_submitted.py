import traceback
import copy

from django.conf import settings
from django.contrib.auth import get_user_model

from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail_send, )
from utils import (reverse_admin_change_path,)
from ..models import (
    CustomInventory,
)

slack = Slacker(settings.SLACK_TOKEN)
User = get_user_model()


def notify_slack_inventory_item_submitted(data):
    """
    as new Inventory item submitted, inform admin on slack.
    """
    details = "".join([f"- *{v[0]}:* {v[1]} \n" for v in data.get('details_display', [])])
    links = "".join([f"- *{v[0]}:* {v[1]} \n" for v in data.get('links_display', [])])
    msg = (
        f"<!channel> New Inventory item *{data.get('item_name')}* is submitted by *{data.get('created_by_name')}* (User ID: `{data.get('created_by_email')}`). Please review and approve the item!\n\n"
        f"Item details are as follows!\n"
        f"{details}"
        f"\n\n"
        f"{links}"
        f"\n"
    )
    slack.chat.post_message(settings.SLACK_INVENTORY_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_email_inventory_item_submitted(data):
    """
    as new Inventory item submitted, send notification mail.
    """
    qs = User.objects.all()
    qs = qs.filter(
        organization_user__organization_user_role__licenses__license_profile__name=data.get('vendor_name'),
        organization_user__organization_user_role__role__name='Sales/Inventory',
    )
    emails = set(qs.values_list('email', flat=True))
    emails.add(settings.NOTIFICATION_EMAIL_INVENTORY)
    if data.get('created_by_email'):
        emails.add(data.get('created_by_email'))
    for email in emails:
        try:
            mail_send(
                "email/notification_inventory_item_submitted.html",
                data,
                "New Inventory Item.",
                email,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_submitted_task(custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        data = copy.deepcopy(obj.__dict__)
        data = dict()
        data['item_name'] = obj.cultivar.cultivar_name
        data['created_by_email'] = obj.created_by.get('email')
        data['created_by_name'] = obj.created_by.get('name')

        data['details_display'] = {
            'Vendor Name':             obj.vendor_name,
            'Client Code':             obj.client_code,
            'Cultivar Name':           obj.cultivar.cultivar_name,
            'Cultivar Type':           obj.cultivar.cultivar_type,
            'Product Category':        obj.category_name,
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
        }.items()

        data['links_display'] = {
            'Admin Link': f'https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}',
        }.items()

        notify_slack_inventory_item_submitted(data)
        notify_email_inventory_item_submitted(data)
