
"""
All periodic tasks related to brand.
"""
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import  timezone

from .models import License

@periodic_task(run_every=(crontab(hour=[1], minute=0)), options={'queue': 'general'})
def update_expired_licence_status():
    """
    Update expired licence status to 'expired'.
    """
    qs = License.objects.filter(expiration_date__lt=timezone.now())
    qs.update(status='expired')