import traceback

from django.conf import settings
from django.contrib.auth import get_user_model

from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail_send,)
from utils import (reverse_admin_change_path,)

from ..models import (
    InventoryItemEdit,
)

slack = Slacker(settings.SLACK_TOKEN)
User = get_user_model()


def notify_slack_inventory_item_change_approved(data):
    """
    as new Inventory item approved, inform admin on slack.
    """
    diff = "".join([ f"- *{v[0]}:* {v[1]} => {v[2]}\n" for v in data.get('diff_display', [])])
    msg = (f"<!channel>Changes for inventory item *{data.get('item_name')}* (sku: `{data.get('item_sku')}`) is"
        f" approved by *{data.get('approved_by_name')}* (User ID: `{data.get('approved_by_email')}`). Please review and approve the changes!\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"changes are as follows!\n"
        f"{diff}"
        f"\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
        f"- *Zoho Inventory Item Link:* {data.get('zoho_item_link')}\n"
        f"- *Webapp Item Link:* {data.get('webapp_item_link')}\n"

    )
    slack.chat.post_message(settings.SLACK_INVENTORY_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_email_inventory_item_change_approved(data):
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
                "email/notification_inventory_item_change_approved.html",
                data,
                "New Inventory Item.",
                email,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_change_approved_task(custom_inventory_id):
    qs = InventoryItemEdit.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        if obj.status == 'pending_for_approval':
            item = obj.item
            data = {}
            data['item_name'] = str(item)
            data['item_sku'] = item.sku
            data['vendor_name'] = item.cf_vendor_name
            data['diff_display'] = obj.get_display_diff_data().values()
            data['approved_by_email'] = obj.approved_by.get('email')
            data['approved_by_name'] = obj.approved_by.get('name')
            data['created_by_email'] = obj.created_by.get('email')
            data['created_by_name'] = obj.created_by.get('name')
            data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
            data['zoho_item_link'] = f"https://inventory.zoho.com/app#/inventory/items/{obj.item.item_id}"
            data['webapp_item_link'] = f"{settings.FRONTEND_DOMAIN_NAME}/marketplace/{obj.item.item_id}/item/"
            # if obj.crm_vendor_id:
            #     data['crm_vendor_link'] = f"{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Vendors/{obj.crm_vendor_id}"
            notify_slack_inventory_item_change_approved(data)
            notify_email_inventory_item_change_approved(data)