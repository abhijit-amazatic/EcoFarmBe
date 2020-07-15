
"""
All periodic tasks related to integrations. 
"""
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app

from inventory.models import (Inventory, )
from .crm import (insert_users, insert_vendors)
from .inventory import (fetch_inventory, )

def fetch(inventory_name):
    """
    Wrapper defination to fetch inventory.
    """
    try:
        inventory_before = Inventory.objects.all().delete()
        fetch_inventory(inventory_name, days=150)
        inventory_after = Inventory.objects.all().count()
        return {'status_code': 200,
                'deleted': inventory_before[0],
                'inserted': inventory_after}
    except Exception as exc:
        return {'status_code': 400,
                'error': exc}

@periodic_task(run_every=(crontab(hour=[9], minute=0)), options={'queue': 'general'})
def fetch_inventory_efd_on_interval():
    """
    Update inventory on every interval from Zoho Inventory.
    """
    return fetch('inventory_efd')

@periodic_task(run_every=(crontab(hour=[10], minute=0)), options={'queue': 'general'})
def fetch_inventory_efl_on_interval():
    """
    Update inventory on every interval from Zoho Inventory.
    """
    return fetch('inventory_efl')
