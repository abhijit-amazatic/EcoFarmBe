
"""
All periodic tasks related to integrations. 
"""
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app
from core.settings import (NUMBER_OF_DAYS_TO_FETCH_INVENTORY)

from inventory.models import (Inventory, )
from labtest.models import (LabTest, )
from .crm import (insert_users, insert_vendors,
                  fetch_labtests, update_in_crm, update_license)
from .inventory import (fetch_inventory, )
from .books import (send_estimate_to_sign, )
from .crm import (fetch_cultivars, fetch_licenses)
from integration.apps.bcc import (post_licenses_to_crm, )


def get_price_data():
    """
    Get price data.
    """
    response = dict()
    price_data = Inventory.objects.values('item_id', 'price')
    for item in price_data.iterator():
        response[item['item_id']] = item['price']
    return response
    
@periodic_task(run_every=(crontab(hour=[9], minute=0)), options={'queue': 'general'})
def fetch_inventory_on_interval():
    """
    Update inventory on every interval from Zoho Inventory.
    """
    try:
        days = int(NUMBER_OF_DAYS_TO_FETCH_INVENTORY)
        price_data = get_price_data()
        # inventory_before = Inventory.objects.all().delete()
        fetch_cultivars(days=days)
        fetch_labtests(days=days)
        licenses = fetch_licenses()
        labtests = LabTest.objects.all().count()
        fetch_inventory('inventory_efd', days=days, price_data=price_data)
        fetch_inventory('inventory_efl', days=days, price_data=price_data)
        inventory_after = Inventory.objects.all().count()
        return {'status_code': 200,
                'labtest': labtests,
        #        'deleted': inventory_before[0],
                'inserted': inventory_after,
                'licenses': licenses}
    except Exception as exc:
        print(exc)
        return {'status_code': 400,
                'error': exc}

@app.task(queue="general")
def send_estimate(estimate_id, contact_id):
    """
    Send estimate for sign.
    """
    return send_estimate_to_sign(estimate_id, contact_id)

@periodic_task(run_every=(crontab(day_of_week='sun', hour=[8], minute=0)), options={'queue': 'general'})
def fetch_bcc_licenses():
    """
    Fetch BCC licenses and post to crm.
    """
    return post_licenses_to_crm()

@app.task(queue="general")
def update_in_crm_task(module, record_id):
    update_in_crm(module, record_id)

@app.task(queue="general")
def update_license_task(dba, license_id):
    update_license(dba=dba, license=None, license_id=license_id)