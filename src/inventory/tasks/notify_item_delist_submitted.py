import traceback

from django.conf import settings
from django.contrib.auth import get_user_model

from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail_send,)
from utils import (reverse_admin_change_path,)

from ..models import (
    InventoryItemDelist,
)

slack = Slacker(settings.SLACK_TOKEN)
User = get_user_model()


def notify_slack_inventory_item_delist_submitted(data):
    """
    slack notification for Inventory item delisting reqest.
    """
    details = "".join([ f"- *{v[0]}:* {v[1]} \n" for v in data.get('details_display', [])])
    msg = (f"<!channel> Delist request for inventory item *{data.get('item_name')}* (sku: `{data.get('item_sku')}`) is"
        f" submitted by *{data.get('created_by_name')}* (User ID: `{data.get('created_by_email')}`). Please review and approve the item delisting!\n"

        f"Item details are as follows!\n"
        f"{details}"
        f"\n\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
        f"- *Zoho Inventory Item Link:* {data.get('zoho_item_link')}\n"
        f"- *Webapp Item Link:* {data.get('webapp_item_link')}\n"

    )
    slack.chat.post_message(
        settings.SLACK_ITEM_DELIST_CHANNEL,
        msg, as_user=False,
        username=settings.BOT_NAME,
        icon_url=settings.BOT_ICON_URL
    )

def notify_email_inventory_item_delist_submitted(data):
    """
    Inventory item delisting reqest notification mail.
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
                "email/notification_inventory_item_delist_submitted.html",
                data,
                "New Inventory Item.",
                email,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_delist_submitted_task(custom_delist_req_id):
    qs = InventoryItemDelist.objects.filter(id=custom_delist_req_id)
    if qs.exists():
        obj = qs.first()
        if obj.status == 'pending_for_approval':
            item = obj.item
            data = {}
            data['item_name'] = obj.item_data.get('name')
            data['item_sku'] = obj.item_data.get('sku')
            data['vendor_name'] = obj.item_data.get('cf_vendor_name')

            data['details_display'] = {
                'Vendor Name': item.cf_vendor_name,
                'Client Code': item.cf_client_code,
                'Cultivar Name': obj.cultivar_name,
                'Cultivar Type': item.cf_cultivar_type,
                'Available Stock': item.available_stock,
                'Marketplace Price': "${:,.2f}".format(item.price) if item.price else '',
                'Marketplace Status': item.cf_status,
            }.items()

            data['created_by_email'] = obj.created_by.get('email')
            data['created_by_name'] = obj.created_by.get('name')
            data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
            if item:
                data['zoho_item_link'] = f"https://inventory.zoho.com/app#/inventory/items/{obj.item.item_id}"
                data['webapp_item_link'] = f"{settings.FRONTEND_DOMAIN_NAME.rstrip('/')}/marketplace/{obj.item.item_id}/item/"

            notify_slack_inventory_item_delist_submitted(data)
            notify_email_inventory_item_delist_submitted(data)            # notify_email_inventory_item_approved(data)

