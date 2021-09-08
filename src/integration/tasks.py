
"""
All periodic tasks related to integrations. 
"""
from datetime import datetime, timedelta
from django.core.exceptions import (ObjectDoesNotExist,)
from celery.task import periodic_task
from celery.schedules import crontab
from core.celery import app
from core.settings import (NUMBER_OF_DAYS_TO_FETCH_INVENTORY,PRODUCTION)

from inventory.models import (Inventory, )
from labtest.models import (LabTest, )
from brand.models import (License)
from .crm import (insert_users, fetch_labtests,
                  update_in_crm, update_license)
from .inventory import (fetch_inventory, fetch_inventory_from_list)
from .books import (send_estimate_to_sign, create_customer_in_books)
from .crm import (fetch_cultivars, fetch_licenses, insert_records)
from  .sign import (upload_pdf_box,)
from .box import(
    get_shared_link,
)
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
def insert_record_to_crm(license_id, is_update=False):
    """
    Insert record to crm and create/update customer and vendor to books.
    """
    insert_records(id=license_id, is_update=is_update)
    create_customer_in_books(id=license_id)


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


@app.task(queue="urgent")
def upload_agreement_pdf_to_box(request_id, folder_id, file_name, license_number):
    """
    Upload document to box.
    """
    file_id = upload_pdf_box(request_id, folder_id, file_name, is_agreement=True)
    if license_number:
        obj = License.objects.order_by('-created_on').filter(license_number=license_number).select_related('license_profile').first()
        if obj:
            if 'agreement' in file_name.lower():
                try:
                    obj.license_profile.agreement_link = get_shared_link(file_id)
                except ObjectDoesNotExist:
                    pass
                else:
                    obj.license_profile.save()
            elif 'w-9' in file_name.lower():
                obj.uploaded_w9_to = get_shared_link(file_id)
                obj.save()

@app.task(queue="urgent")
def fetch_inventory_from_list_task(inventory_name, inventory_list, is_composite=False):
    fetch_inventory_from_list(inventory_name, inventory_list, is_composite)