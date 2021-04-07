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


def notify_slack_inventory_item_added(data):
    """
    as new Inventory item added, inform admin on slack.
    """
    msg = (f"<!channel>New Inventory item is Submitted by user associated with the EmailID `{data.get('user_email')}`. Please review and approve the item!\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"- *Client Code:* {data.get('client_code')}\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Cultivar Type:* {data.get('cultivar_type')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Farm Price:* {data.get('farm_price_formated')}\n"
        f"- *Pricing Position:* {data.get('pricing_position')}\n"
        # f"- *Min Qty Purchase:* {data.get('minimum_order_quantity')}\n"
        f"- *Seller Grade Estimate:* {data.get('grade_estimate')}\n"
        f"- *Need Testing:* { 'Yes' if data.get('need_lab_testing_service') else 'No'}\n"
        f"- *Batch Availability Date:* {data.get('batch_availability_date')}\n"
        f"- *Harvest Date:* {data.get('harvest_date')}\n"
        f"- *Batch Quality Notes:* {data.get('product_quality_notes')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
    )
    slack.chat.post_message(settings.SLACK_INVENTORY_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_email_inventory_item_added(data):
    """
    as new Inventory item added, send notification mail.
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
                "email/notification_inventory_item_added.html",
                data,
                "New Inventory Item.",
                email,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_added_task(email, custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        data = copy.deepcopy(obj.__dict__)
        data['cultivar_name'] = obj.cultivar.cultivar_name
        data['cultivar_type'] = obj.cultivar.cultivar_type
        data['user_email'] = email
        data['created_by_email'] = obj.created_by.get('email')
        data['created_by_name'] = obj.created_by.get('name')
        data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
        if obj.farm_ask_price:
            data['farm_price_formated'] = "${:,.2f}".format(obj.farm_ask_price)
        notify_slack_inventory_item_added(data)
        notify_email_inventory_item_added(data)
