
"""
All tasks related to inventory. 
"""
import re
import traceback
import copy
from django.conf import settings

from celery.task import periodic_task
from celery.schedules import crontab
from slacker import Slacker

from core.celery import app
from core.mailer import mail, mail_send

from integration.books import (create_purchase_order, submit_purchase_order)
from brand.models import (LicenseProfile, )
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

@app.task(queue="general")
def create_approved_item_po(custom_inventory_id, client_code, retry=3):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    if item.status == 'approved':
        try:
            lp_obj = LicenseProfile.objects.get(name=item.vendor_name)
        except Exception:
            license_number = ''
        else:
            license_number = lp_obj.license.license_number
        data = {
            # "vendor_id": "460000000026049",
            # "purchaseorder_number": "PO-00001",
            'vendor_name': item.vendor_name,
            # "gst_treatment": "business_gst",
            # "tax_treatment": "vat_registered",
            # "gst_no": "22AAAAA0000A1Z5",
            # "source_of_supply": "AP",
            # "destination_of_supply": "TN",
            # "place_of_supply": "DU",
            # # "pricebook_id": 460000000026089,
            # "reference_number": "ER/0034",
            # "billing_address_id": "460000000017491",
            # "template_id": "460000000011003",
            # "date": "2014-02-10",
            # "delivery_date": "2014-02-10",
            # "exchange_rate": 1,
            # # "discount": "10",
            # # "discount_account_id": "460000000011105",
            # # "is_discount_before_tax": true,
            # # "is_inclusive_tax": False,
            # "notes": "Please deliver as soon as possible.",
            # "terms": "Thanks for your business.",
            # "salesorder_id": "460000124728314",
            "line_items": [
                {
                    "item_id": item.zoho_item_id,
                    # "account_id": "2155380000000448337",
                    # "name": item.cultivar.cultivar_name,
                    "sku": item.sku,
                    # "rate": 112,
                    "quantity": int(item.quantity_available),
                    # "item_order": 0,
                    # "tax_treatment_code": "uae_others",
                    # "tags": [
                    #     {}
                    # ],
                    # "project_id": 90300000087378
                }
            ],
            "custom_fields": [
                {
                    "api_name": "cf_client_code",
                    "value": client_code,
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
        #     data['custom_fields'].append({)                # {
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
            create_approved_item_po.apply_async((item.id, client_code, retry-1), countdown=5)


@app.task(queue="general")
def create_duplicate_crm_vendor_from_account_(vendor_name,):
    pass