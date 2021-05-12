from django.dispatch import receiver
from django.db.models import signals
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
