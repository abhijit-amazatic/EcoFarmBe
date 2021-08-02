from django.apps import apps
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver


PageMeta = apps.get_model('seo', 'PageMeta')

@receiver(signals.pre_save, sender=PageMeta)
def pre_save_page_meta(sender, instance, **kwargs):
    url = instance.page_url.strip()
    if not url.startswith('/'):
        url = '/' + url
    if not url.endswith('/'):
        url = url + '/'
    instance.page_url = url