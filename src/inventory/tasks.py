
"""
All tasks related to inventory. 
"""
import re
import traceback
import copy
from django.conf import settings
from django.shortcuts import reverse

from celery.task import periodic_task
from celery.schedules import crontab
from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail, mail_send)

from integration.books import (create_purchase_order, submit_purchase_order)
from brand.models import (LicenseProfile, )

from .task_helpers import (
    create_duplicate_crm_vendor_from_crm_account,
    get_custom_inventory_data_from_crm_vendor,
    get_custom_inventory_data_from_crm_account,
)
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
        f"- *Need Lab Test Yes / No:* { 'Yes' if data.get('need_lab_testing_service') else 'No'}\n"
        f"- *Batch Availability Date:* {data.get('batch_availability_date')}\n"
        f"- *Grade Estimate:* {data.get('grade_estimate')}\n"
        f"- *Batch Quality Notes:* {data.get('product_quality_notes')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
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

def reverse_admin_change_path(obj):
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=(obj.id,),
    )

@app.task(queue="general")
def notify_inventory_item_added(email, custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        data = copy.deepcopy(obj.__dict__)
        data['cultivar_name'] = obj.cultivar.cultivar_name
        data['cultivar_type'] = obj.cultivar.cultivar_type
        data['user_email'] = email
        data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
        notify_slack_inventory_item_added(data)
        notify_email_inventory_item_added(data)

@app.task(queue="general")
def create_approved_item_po(custom_inventory_id, retry=6):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    if item.status == 'approved':
        try:
            lp_obj = LicenseProfile.objects.get(name=item.vendor_name)
        except Exception:
            license_number = ''
        else:
            license_number = lp_obj.license.license_number
        data = {
            'vendor_name': item.vendor_name,
            "line_items": [
                {
                    "sku": item.sku,
                    "quantity": int(item.quantity_available),
                }
            ],
            "custom_fields": [
                {
                    "api_name": "cf_client_code",
                    "value": item.client_code,
                },
                {
                    "api_name": "cf_billing_published",
                    "value": True,
                },
            ],
        }

        if license_number:
            data['custom_fields'].append({
                "api_name": "cf_client_license",
                "value": license_number,
            })

        # if procurement_rep_id:
        #     data['custom_fields'].append({
        #         "api_name": "cf_procurement_rep",
        #         "value": "",
        #     })

        result = create_purchase_order(data, params={})
        if result.get('code') == 0:
            item.books_po_id = result.get('purchaseorder', {}).get('purchaseorder_id')
            item.po_number = result.get('purchaseorder', {}).get('purchaseorder_number')
            item.save()
            submit_purchase_order(item.books_po_id)
        elif retry:
            create_approved_item_po.apply_async((item.id, retry-1), countdown=15)


@app.task(queue="general")
def create_duplicate_crm_vendor_from_crm_account_task(vendor_name):
    create_duplicate_crm_vendor_from_crm_account(vendor_name)

@app.task(queue="general")
def get_custom_inventory_data_from_crm(custom_inventory_id):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    if not item.client_code:
        get_custom_inventory_data_from_crm_vendor(item)
    if not item.client_code:
        get_custom_inventory_data_from_crm_account(item)
    item.save()