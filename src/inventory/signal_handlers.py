import copy
import json
import datetime
from django.dispatch import receiver
from django.db.models import signals
from django.core import serializers
from django.forms.models import model_to_dict
from django.apps import apps


@receiver(signals.post_save, sender=apps.get_model('inventory', 'CustomInventory'))
def post_save_custom_inventory(sender, instance, created, **kwargs):
    if created:
        l_p = instance.license_profile
        if l_p:
            if  l_p.license.profile_category == 'nursery' and instance.category_name in ['Clones',]:
                    instance.zoho_organization = 'efn'
                    instance.save()
            elif l_p.license.legal_business_name == 'EFL, LLC':
                instance.zoho_organization = 'efl'
                instance.save()
            else:
                instance.zoho_organization = 'efd'
                instance.save()

@receiver(signals.pre_save, sender=apps.get_model('inventory', 'InventoryItemDelist'))
def pre_save_item_deletion_request(sender, instance, **kwargs):
    if not instance.status == 'approved':
        item = instance.item
        if item:
            data = {
                k: str(v) if isinstance(v, datetime.date) or isinstance(v, datetime.time) else v
                for k, v in item.__dict__.items()
                if not k.startswith('_')
            }
            instance.name = item.name
            instance.item_data = data
            instance.vendor_name = item.cf_vendor_name
            instance.cultivar_name = getattr(item.cultivar, 'cultivar_name') if item.cultivar else ''
            instance.sku = item.sku
            instance.zoho_item_id = item.item_id
