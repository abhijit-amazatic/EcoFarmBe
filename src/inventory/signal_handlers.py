from django.dispatch import receiver
from django.db.models import signals
from django.apps import apps

from simple_history.models import HistoricalRecords
from simple_history.signals import (
    pre_create_historical_record,
    post_create_historical_record
)


Inventory = apps.get_model('inventory', 'Inventory')
HistoricalInventory = apps.get_model('inventory', 'HistoricalInventory')

# @receiver(pre_create_historical_record, sender=HistoricalInventory)
# def add_user_info(sender, **kwargs):
#     history_instance = kwargs['history_instance']
#     if hasattr(HistoricalRecords, 'thread'):
#         history_instance.ip_address = HistoricalRecords.thread.request.META['REMOTE_ADDR']


@receiver(signals.pre_save, sender=Inventory)
def pre_save_inventory(sender, instance, **kwargs):
    """
    Deletes old file.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return
        else:
            od = old_instance.__dict__
            cd = instance.__dict__
            diff = {
                k: (repr(od[k]), repr(v)) if isinstance(od[k], str) else (od[k], v)
                for k, v in cd.items()
                if not k.startswith('_') and k not in ('created_time', 'last_modified_time') and (od[k] or v) and getattr(old_instance, k, '') != getattr(instance, k, '')
            }
            diff_msg = '  |  '.join([f"{k}: {v[0]} to {v[1]}" for k, v in diff.items()])
            instance._change_reason = diff_msg
            if diff_msg:
                if hasattr(instance, 'skip_history_when_saving'):
                    del instance.skip_history_when_saving
            else:
                instance.skip_history_when_saving = True

@receiver(signals.post_save, sender=Inventory)
def post_save_inventory(sender, instance, **kwargs):
    """
    Deletes old file.
    """
    if hasattr(instance, 'skip_history_when_saving'):
        del instance.skip_history_when_saving

