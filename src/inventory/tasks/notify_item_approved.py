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
        f"<!channel> Inventory item *{data.get('item_name')}* (sku: `{data.get('item_sku')}`) is"
        f" approved by *{data.get('approved_by_name')}* (User ID: `{data.get('approved_by_email')}`).\n\n"
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
            data['item_name'] = obj.item_name
            data['item_sku'] = obj.sku
            data['approved_by_email'] = obj.approved_by.get('email')
            data['approved_by_name'] = obj.approved_by.get('name')
            data['created_by_email'] = obj.created_by.get('email')
            data['created_by_name'] = obj.created_by.get('name')


            details_display = {
                'transportation':           ('Transportation / Sample Pickup',          obj.transportation,                    ),
                'pick_contact_time':        ('Best time to call to arrange for pickup', obj.pick_contact_time_formatted        ),
                'vendor_name':              ('Vendor Name',                             obj.vendor_name                        ),
                'client_code':              ('Client Code',                             obj.client_code                        ),
                'category_name':            ('Product Category',                        obj.category_name                      ),
                'mfg_batch_id':             ('Batch ID',                                obj.mfg_batch_id                       ),
                'cannabinoid_type':         ('Cannabinoid type',                        obj.cannabinoid_type                   ),
                'cannabinoid_percentage':   ('Cannabinoid Percentage',                  obj.cannabinoid_percentage_formatted   ),
                'cultivar_name':            ('Cultivar Name',                           obj.get_cultivar_name                  ),
                'cultivar_type':            ('Cultivar Type',                           obj.get_cultivar_type                  ),
                'sku':                      ('SKU',                                     obj.sku                                ),
                'marketplace_status':       ('Marketplace Status',                      obj.marketplace_status                 ),
                'quantity_available':       ('Quantity Available',                      obj.quantity_available                 ),
                'farm_price':               ('Farm Price',                              obj.farm_ask_price_formatted           ),
                'pricing_position':         ('Pricing Position',                        obj.pricing_position                   ),
                # 'minimum_order_quantity':   ('Min Qty Purchase',                        obj.minimum_order_quantity             ),
                'grade_estimate':           ('Seller Grade Estimate',                   obj.grade_estimate                     ),
                'need_lab_testing_service': ('Need Testing',                            obj.need_lab_testing_service_formatted ),
                'batch_availability_date':  ('Batch Availability Date',                 obj.batch_availability_date            ),
                'harvest_date':             ('Harvest Date',                            obj.harvest_date                       ),
                'manufacturing_date':       ('Manufacturing Date',                      obj.manufacturing_date                 ),
                'total_batch_quantity':     ('Total Batch Quantity',                    obj.total_batch_quantity               ),
                'trim_used':                ('Trim Used (lb)',                          obj.trim_used                          ),
                'rooting_days':             ('Rooting Days',                            obj.rooting_days,                      ),
                'clone_size':               ('Clone Size (inch)',                       obj.clone_size,                        ),
                'product_quality_notes':    ('Batch Quality Notes',                     obj.product_quality_notes              ),
            }


            category_common_fields = (
                'vendor_name',
                'client_code',
                'category_name',
                'sku',
                'marketplace_status',
                'quantity_available',
                'farm_price',
                'pricing_position',
                'need_lab_testing_service',
                'batch_availability_date',
                'product_quality_notes',
            )
            category_specific_fields = ( )

            if obj.category_group in ('Flowers', 'Trims', 'Kief' ''):
                category_specific_fields = (
                    'cultivar_name',
                    'cultivar_type',
                    'grade_estimate',
                    'harvest_date',
                )
            elif obj.category_group in ('Isolates', 'Distillates'):
                category_specific_fields = (
                    'mfg_batch_id',
                    'cannabinoid_type',
                    'cannabinoid_percentage',
                    'manufacturing_date',
                    'total_batch_quantity',
                    'trim_used',
                )
            elif obj.category_group in ('Concentrates', 'Terpenes'):
                category_specific_fields = (
                    'cultivar_name',
                    'cultivar_type',
                    'manufacturing_date',
                    'total_batch_quantity',
                    'trim_used',
                )
            elif obj.category_group in ('Clones'):
                category_specific_fields = (
                    'cultivar_name',
                    'cultivar_type',
                    'batch_availability_date',
                    'rooting_days',
                    'clone_size',
                )

            data['details_display'] = [
                v for k, v in details_display.items() if k in category_common_fields+category_specific_fields
            ]

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
                    logistic_specific_fields = (
                        'transportation',
                        'pick_contact_time',
                        'vendor_name',
                        'client_code',
                        'category_name',
                        'cultivar_name',
                        'quantity_available',
                    )

                    data['details_display'] = [v for k, v in details_display.items() if k in logistic_specific_fields]

                    data['links_display'] = {
                        'Admin Link':      f'https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}',
                        'CRM Vendor Link': f'{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Vendors/{obj.crm_vendor_id}' if obj.crm_vendor_id else '',
                    }.items()

                    notify_logistics_slack_inventory_item_approved(data)
                    notify_logistics_email_inventory_item_approved(data)

