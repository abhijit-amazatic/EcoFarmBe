import copy
import json
import datetime
from django.dispatch import receiver
from django.db.models import signals
from django.forms.models import model_to_dict
from django.apps import apps



@receiver(signals.pre_save, sender=apps.get_model('compliance_binder', 'BinderLicense'))
def pre_save_item_deletion_request(sender, instance, **kwargs):
    if instance.profile_license:
        license_data = model_to_dict(instance.profile_license)
        instance.__dict__.update({k:v for k, v in license_data.items() if k in instance.__dict__.keys() and k != 'id'})
