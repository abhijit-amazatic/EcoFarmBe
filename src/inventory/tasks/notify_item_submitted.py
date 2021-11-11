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
        data['item_name'] = obj.item_name
        data['created_by_email'] = obj.created_by.get('email')
        data['created_by_name'] = obj.created_by.get('name')

        u = obj.unit

        details_display = {
            'vendor_name':              ('Vendor Name',              obj.vendor_name                        ),
            'client_code':              ('Client Code',              obj.client_code                        ),
            'category_name':            ('Product Category',         obj.category_name                      ),
            'mfg_batch_id':             ('Batch ID',                 obj.mfg_batch_id                       ),
            'cannabinoid_type':         ('Cannabinoid type',         obj.cannabinoid_type                   ),
            'cannabinoid_percentage':   ('Cannabinoid Percentage',   obj.cannabinoid_percentage_formatted   ),
            'cultivar_name':            ('Cultivar Name',            obj.get_cultivar_name                  ),
            'cultivar_type':            ('Cultivar Type',            obj.get_cultivar_type                  ),
            'marketplace_status':       ('Marketplace Status',       obj.marketplace_status                 ),
            'quantity_available':       ('Quantity Available',       obj.quantity_available                 ),
            'mcsp_fee':                 (f'Mcsp Fee ($/{u})',        obj.mcsp_fee_formatted                 ),
            'cultivation_tax':          (f'Cultivation Tax ($/{u})', obj.cultivation_tax_formatted          ),
            'farm_price':               ('Farm Price',               obj.farm_ask_price_formatted           ),
            'pricing_position':         ('Pricing Position',         obj.pricing_position                   ),
            # 'minimum_order_quantity':   ('Min Qty Purchase',         obj.minimum_order_quantity             ),
            'grade_estimate':           ('Seller Grade Estimate',    obj.grade_estimate                     ),
            'need_lab_testing_service': ('Need Testing',             obj.need_lab_testing_service_formatted ),
            'batch_availability_date':  ('Batch Availability Date',  obj.batch_availability_date            ),
            'harvest_date':             ('Harvest Date',             obj.harvest_date                       ),
            'manufacturing_date':       ('Manufacturing Date',       obj.manufacturing_date                 ),
            'biomass_type':             ('Biomass Type',             obj.biomass_type                       ),
            'total_batch_quantity':     ('Total Batch Quantity',     obj.total_batch_quantity_formatted     ),
            'biomass_input_g':          ('Boimass Input (g)',        obj.biomass_input_g_formatted          ),
            'rooting_days':             ('Rooting Days',             obj.rooting_days,                      ),
            'clone_size':               ('Clone Size (inch)',        obj.clone_size,                        ),
            'product_quality_notes':    ('Batch Quality Notes',      obj.product_quality_notes              ),
        }


        category_common_fields = (
            'vendor_name',
            'client_code',
            'category_name',
            'marketplace_status',
            'quantity_available',
            'mcsp_fee',
            'cultivation_tax',
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
                'biomass_type',
                'total_batch_quantity',
                'biomass_input_g',
            )
        elif obj.category_group in ('Concentrates', 'Terpenes'):
            category_specific_fields = (
                'cultivar_name',
                'cultivar_type',
                'manufacturing_date',
                'biomass_type',
                'total_batch_quantity',
                'biomass_input_g',
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
            'Admin Link': f'https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}',
        }.items()

        notify_slack_inventory_item_submitted(data)
        notify_email_inventory_item_submitted(data)
