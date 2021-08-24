
"""
All periodic tasks related to integrations. 
"""
from datetime import datetime, timedelta
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app
from core.settings import (NUMBER_OF_DAYS_TO_FETCH_INVENTORY,PRODUCTION)

from inventory.models import (Inventory, )
from labtest.models import (LabTest, )
from .crm import (insert_users, fetch_labtests,
                  update_in_crm, update_license)
from .inventory import (fetch_inventory, )
from .books import (send_estimate_to_sign, )
from .crm import (fetch_cultivars, fetch_licenses)
from integration.apps.bcc import (post_licenses_to_crm, )
from bill.utils import (delete_estimate, )
from drf_api_logger.models import APILogsModel

def get_price_data():
    """
    Get price data.
    """
    response = dict()
    price_data = Inventory.objects.values('item_id', 'price')
    for item in price_data.iterator():
        response[item['item_id']] = item['price']
    return response
    
# @periodic_task(run_every=(crontab(hour=[9], minute=0)), options={'queue': 'general'})
@app.task(queue="general")
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
        # Commenting below only for staging. We do not have test book organization for staging.
        # if PRODUCTION:
        #     fetch_inventory('inventory_efl', days=days, price_data=price_data)
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
def send_estimate(organization_name, estimate_id, contact_id):
    """
    Send estimate for sign.
    """
    return send_estimate_to_sign(organization_name, estimate_id, contact_id)

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

@app.task(queue="urgent")
def delete_estimate_task(customer_name):
    is_deleted = delete_estimate(customer_name=customer_name)
    if not is_deleted:
        print(f'Estimate of {customer_name} cannot be deleted from db.')

@periodic_task(run_every=(crontab(day_of_week='sun', hour=[7], minute=0)), options={'queue': 'general'})
def remove_logger_data():
    """
    Keep logger data for 15 day window.
    """
    days_diff = datetime.today() - timedelta(days=15)
    logs_to_remove = APILogsModel.objects.exclude(added_on__gte=days_diff)
    if logs_to_remove:
        logs_to_remove.delete()
         
     
     
    
        
