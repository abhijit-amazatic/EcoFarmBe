
"""
All tasks related to inventory. 
"""
import re
import traceback
import copy
import datetime
import pytz
import io
import csv

from django.conf import settings
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from celery.task import periodic_task
from celery.schedules import crontab
from slacker import Slacker

from core.celery import (app,)
from core.mailer import (mail, mail_send)

from integration.box import (upload_file, upload_file_stream, )
from integration.books import (create_purchase_order, submit_purchase_order)
from integration.inventory import (get_inventory_obj,get_inventory_summary,)
from brand.models import (LicenseProfile, )

from .task_helpers import (
    create_duplicate_crm_vendor_from_crm_account,
    get_custom_inventory_data_from_crm_vendor,
    get_custom_inventory_data_from_crm_account,
)
from .models import (
    Inventory,
    CustomInventory,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
)

slack = Slacker(settings.SLACK_TOKEN)
User = get_user_model()

def notify_slack_inventory_item_added(data):
    """
    as new Inventory item added, inform admin on slack.
    """
    msg = (f"<!channel>New Inventory item is Submitted by user associated with the EmailID `{data.get('user_email')}`. Please review and approve the item!\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"- *Client Code:* {data.get('client_code')}\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Cultivar Type:* {data.get('cultivar_type')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Farm Price:* {data.get('farm_price_formated')}\n"
        f"- *Pricing Position:* {data.get('pricing_position')}\n"
        # f"- *Min Qty Purchase:* {data.get('minimum_order_quantity')}\n"
        f"- *Seller Grade Estimate:* {data.get('grade_estimate')}\n"
        f"- *Need Testing:* { 'Yes' if data.get('need_lab_testing_service') else 'No'}\n"
        f"- *Batch Availability Date:* {data.get('batch_availability_date')}\n"
        f"- *Harvest Date:* {data.get('harvest_date')}\n"
        f"- *Batch Quality Notes:* {data.get('product_quality_notes')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
    )
    slack.chat.post_message(settings.SLACK_INVENTORY_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_email_inventory_item_added(data):
    """
    as new Inventory item added, send notification mail.
    """
    qs = User.objects.all()
    qs = qs.filter(
        organization_user__organization_user_role__licenses__license_profile__name=data.get('vendor_name'),
        organization_user__organization_user_role__role__name='Sales/Inventory',
    )
    emails = set(qs.values_list('email', flat=True))
    emails.add(settings.NOTIFICATION_EMAIL_INVENTORY)
    if data.get('created_by_email'):
        emails.add(data.get('created_by_email'))
    for email in emails:
        try:
            mail_send(
                "notification_inventory_item_added.html",
                data,
                "New Inventory Item.",
                email,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)

def reverse_admin_change_path(obj):
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=(obj.id,),
    )

@app.task(queue="general")
def notify_inventory_item_added(email, custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        data = copy.deepcopy(obj.__dict__)
        data['cultivar_name'] = obj.cultivar.cultivar_name
        data['cultivar_type'] = obj.cultivar.cultivar_type
        data['user_email'] = email
        data['created_by_email'] = obj.created_by.get('email')
        data['created_by_name'] = obj.created_by.get('name')
        data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
        if obj.farm_ask_price:
            data['farm_price_formated'] = "${:,.2f}".format(obj.farm_ask_price)
        notify_slack_inventory_item_added(data)
        notify_email_inventory_item_added(data)



def notify_slack_inventory_item_approved(data):
    """
    as new Inventory item approved, inform admin on slack.
    """
    msg = (f"<!channel>Inventory item is approved by *{data.get('approved_by_name')}* (User ID: `{data.get('approved_by_email')}`).\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"- *Client Code:* {data.get('client_code')}\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Cultivar Type:* {data.get('cultivar_type')}\n"
        f"- *SKU:* {data.get('sku')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Farm Price:* {data.get('farm_price_formated')}\n"
        f"- *Pricing Position:* {data.get('pricing_position')}\n"
        # f"- *Min Qty Purchase:* {data.get('minimum_order_quantity')}\n"
        f"- *Seller Grade Estimate:* {data.get('grade_estimate')}\n"
        f"- *Need Testing:* { 'Yes' if data.get('need_lab_testing_service') else 'No'}\n"
        f"- *Batch Availability Date:* {data.get('batch_availability_date')}\n"
        f"- *Harvest Date:* {data.get('harvest_date')}\n"
        f"- *Batch Quality Notes:* {data.get('product_quality_notes')}\n"
        f"- *Procurement Rep:* {data.get('procurement_rep_name')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
        f"- *Zoho Inventory Item Link:* {data.get('zoho_item_link')}\n"
    )
    slack.chat.post_message(settings.SLACK_INVENTORY_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_email_inventory_item_approved(data):
    """
    as new Inventory item approved, send notification mail.
    """
    if data.get('created_by_email'):
        try:
            mail_send(
                "notification_inventory_item_approved.html",
                data,
                "Inventory Item Approved",
                data.get('created_by_email'),
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)

def notify_logistics_slack_inventory_item_approved(data):
    """
    as new Inventory item approved, inform Logistic on slack.
    """
    msg = (f"<!channel>New Inventory item is added. Logistics detail summary for the item is as follows:\n"
        f"- *Transportation / Sample Pickup:* {data.get('transportation')}\n"
        f"- *Best time to call to arrange for pickup:* "
        f"{data.get('best_day')} {data.get('best_time_from')} - {data.get('best_time_to')}\n"
        f"- *Vendor Name:* {data.get('vendor_name')}\n"
        f"- *Client Code:* {data.get('client_code')}\n"
        f"- *Product Category:* {data.get('category_name')}\n"
        f"- *Cultivar Name:* {data.get('cultivar_name')}\n"
        f"- *Quantity:* {data.get('quantity_available')}\n"
        f"- *Admin Link:* {data.get('admin_link')}\n"
        f"- *CRM Vendor Link:* {data.get('crm_vendor_link')}\n"
    )
    slack.chat.post_message(settings.SLACK_LOGISTICS_TRANSPORT_CHANNEL, msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)

def notify_logistics_email_inventory_item_approved(data):
    """
    as new Inventory item approved, send Logistic notification mail.
    """
    if data.get('created_by_email'):
        try:
            mail_send(
                "notification_inventory_item_approved_logistics.html",
                data,
                "New Inventory Item",
                settings.NOTIFICATION_EMAIL_LOGISTICS_TRANSPORT,
            )
        except Exception as e:
            traceback.print_tb(e.__traceback__)


@app.task(queue="general")
def notify_inventory_item_approved(custom_inventory_id):
    qs = CustomInventory.objects.filter(id=custom_inventory_id)
    if qs.exists():
        obj = qs.first()
        if obj.status == 'approved':
            data = copy.deepcopy(obj.__dict__)
            data['cultivar_name'] = obj.cultivar.cultivar_name
            data['cultivar_type'] = obj.cultivar.cultivar_type
            data['admin_link'] = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(obj)}"
            data['approved_by_email'] = obj.approved_by.get('email')
            data['approved_by_name'] = obj.approved_by.get('name')
            data['created_by_email'] = obj.created_by.get('email')
            data['created_by_name'] = obj.created_by.get('name')
            data['zoho_item_link'] = f"https://inventory.zoho.com/app#/inventory/items/{obj.zoho_item_id}"
            data['webapp_item_link'] = f"{settings.FRONTEND_DOMAIN_NAME}/inventory/{obj.zoho_item_id}/item/"
            if obj.farm_ask_price:
                data['farm_price_formated'] = "${:,.2f}".format(obj.farm_ask_price)
            if obj.best_contact_Day_of_week:
                data['best_day'] = obj.best_contact_Day_of_week.title()
            if obj.best_contact_time_from:
                data['best_time_from'] = obj.best_contact_time_from.strftime("%I:%M %p")
            if obj.best_contact_time_to:
                data['best_time_to'] = obj.best_contact_time_to.strftime("%I:%M %p")
            if obj.crm_vendor_id:
                data['crm_vendor_link'] = f"{settings.ZOHO_CRM_URL}/crm/org{settings.CRM_ORGANIZATION_ID}/tab/Vendors/{obj.crm_vendor_id}"
            notify_slack_inventory_item_approved(data)
            notify_logistics_slack_inventory_item_approved(data)
            notify_email_inventory_item_approved(data)
            notify_logistics_email_inventory_item_approved(data)



@app.task(queue="general")
def create_approved_item_po(custom_inventory_id, retry=6):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    if item.status == 'approved':
        try:
            lp_obj = LicenseProfile.objects.get(name=item.vendor_name)
        except Exception:
            license_number = ''
        else:
            license_number = lp_obj.license.license_number

        warehouse_id = None
        inv_obj = get_inventory_obj(inventory_name='inventory_efd',)
        result = inv_obj.list_warehouses()
        if result.get('code') == 0:
            warehouses = result.get("warehouses", [])
            warehouses = [
                warehouse
                for warehouse in warehouses 
                if warehouse.get('warehouse_name', '').strip() == getattr(settings, 'CUSTOM_INVENTORY_WAREHOUSE_NAME', '').strip()
            ]
            if warehouses:
                warehouse_id = warehouses[0].get('warehouse_id')

        item_data = {
            "sku": item.sku,
            "quantity": int(item.quantity_available),
            "rate": 0.0,
        }

        if warehouse_id:
            item_data['warehouse_id'] = warehouse_id

        data = {
            'vendor_name': item.vendor_name,
            "line_items": [item_data],
            "custom_fields": [
                {
                    "api_name": "cf_client_code",
                    "value": item.client_code,
                },
                {
                    "api_name": "cf_billing_published",
                    "value": True,
                },
            ],
        }

        if license_number:
            data['custom_fields'].append({
                "api_name": "cf_client_license",
                "value": license_number,
            })

        # if procurement_rep_id:
        #     data['custom_fields'].append({
        #         "api_name": "cf_procurement_rep",
        #         "value": "",
        #     })

        result = create_purchase_order(data, params={})
        if result.get('code') == 0:
            item.books_po_id = result.get('purchaseorder', {}).get('purchaseorder_id')
            item.po_number = result.get('purchaseorder', {}).get('purchaseorder_number')
            item.save()
            submit_purchase_order(item.books_po_id)
        elif retry:
            create_approved_item_po.apply_async((item.id, retry-1), countdown=15)


@app.task(queue="general")
def create_duplicate_crm_vendor_from_crm_account_task(custom_inventory_id):
    obj = CustomInventory.objects.get(id=custom_inventory_id)
    resp = create_duplicate_crm_vendor_from_crm_account(obj.vendor_name)
    if resp.get('status_code') == 201:
        try:
            vendor_id = resp['response']['data'][0]['details']['id']
        except TypeError:
            vendor_id = resp['response'][0]['id']
        obj.crm_vendor_id = vendor_id
        obj.save()

@app.task(queue="general")
def get_custom_inventory_data_from_crm(custom_inventory_id):
    item = CustomInventory.objects.get(id=custom_inventory_id)
    if not item.client_code:
        get_custom_inventory_data_from_crm_vendor(item)
    if not item.client_code:
        get_custom_inventory_data_from_crm_account(item)
    item.save()

@periodic_task(run_every=(crontab(hour=[8], minute=0)), options={'queue': 'general'})
def county_update_create():
    """
    Save county names.
    """
    categories = Inventory.objects.filter(
        cf_cfi_published=True
    ).values('county_grown').distinct()
    counties = [i['county_grown'] for i in categories if i['county_grown']]
    
    for county in counties:
        obj, created = County.objects.update_or_create(name=county,defaults={'name':county})
        print(created, obj)
    

@periodic_task(run_every=(crontab(hour=[8], minute=0)), options={'queue': 'general'})
def save_daily_aggrigated_summary():
    """
    Save daily inventory  aggrigated summary(without county).
    """
    queryset = Inventory.objects.filter(cf_cfi_published=True)
    summary = get_inventory_summary(queryset)
    fields_data = {
        'date': datetime.datetime.now(pytz.timezone('US/Pacific')).date(),
        'total_thc_max':summary['total_thc_max'],
        'total_thc_min':summary['total_thc_min'],
        'batch_varities':summary['batch_varities'],
        'average':summary['average'],
        'total_value':summary['total_value'],
        'smalls_quantity':summary['smalls_quantity'],
        'tops_quantity':summary['tops_quantity'],
        'total_quantity':summary['total_quantity'],
        'trim_quantity':summary['trim_quantity']
    }
        
    if summary:
        print('saving aggregated summary data for date `%s`:' % (fields_data['date']))
        DailyInventoryAggrigatedSummary.objects.update_or_create(**fields_data)
        
@periodic_task(run_every=(crontab(hour=[8], minute=0)), options={'queue': 'general'})
def save_daily_aggrigated_county_summary():
    """
    Save daily inventory aggrigated summary(with county).
    """
    counties= County.objects.filter().values('name','id')
                
    for county in counties:
        queryset = Inventory.objects.filter(cf_cfi_published=True, county_grown__in=[county['name']])
        summary = get_inventory_summary(queryset)
        fields_data = {
            'date': datetime.datetime.now(pytz.timezone('US/Pacific')).date(),
            'county_id': county['id'],
            'total_thc_max':summary['total_thc_max'],
            'total_thc_min':summary['total_thc_min'],
            'batch_varities':summary['batch_varities'],
            'average':summary['average'],
            'total_value':summary['total_value'],
            'smalls_quantity':summary['smalls_quantity'],
            'tops_quantity':summary['tops_quantity'],
            'total_quantity':summary['total_quantity'],
            'trim_quantity':summary['trim_quantity']
        }
        
        if summary:
            print('saving aggregated summary data for county `%s` and date `%s`:' % (county['name'],fields_data['date']))
            CountyDailySummary.objects.update_or_create(**fields_data)
            
    
@periodic_task(run_every=(crontab(hour=[8], minute=0)), options={'queue': 'general'})
def export_inventory_csv():
    with io.StringIO() as f:
        writer = csv.writer(f)
        qs = Inventory.objects.all()
        file_name = 'Inventory_'+timezone.now().strftime("%Y-%m-%d_%H:%M:%S_%Z")+'.csv'
        if qs.count()>0:
            fields = qs[:1].values()[0].keys()
            writer.writerow(fields)
            writer.writerows(qs.values_list(*fields))
            f.seek(0)
            upload_file_stream(settings.INVENTORY_CSV_UPLOAD_FOLDER_ID, f, file_name)

            
@periodic_task(run_every=(crontab(hour=[9], minute=0)), options={'queue': 'general'})
def export_inventory_aggrigated_csv():
    with io.StringIO() as f:
        writer = csv.writer(f)
        qs = DailyInventoryAggrigatedSummary.objects.filter(date=datetime.datetime.now(pytz.timezone('US/Pacific')).date())
        file_name = 'Aggrigated_Inventory_'+timezone.now().strftime("%Y-%m-%d_%H:%M:%S_%Z")+'.csv'
        if qs.count()>0:
            fields = qs[:1].values()[0].keys()
            writer.writerow(fields)
            writer.writerows(qs.values_list(*fields))
            f.seek(0)
            upload_file_stream(settings.INVENTORY_CSV_UPLOAD_FOLDER_ID, f, file_name)
            
@periodic_task(run_every=(crontab(hour=[9], minute=0)), options={'queue': 'general'})
def export_inventory_aggrigated_county_csv():
    counties= County.objects.filter().values('name','id')
    for county in counties:
        with io.StringIO() as f:
            writer = csv.writer(f)
            qs = CountyDailySummary.objects.filter(date=datetime.datetime.now(pytz.timezone('US/Pacific')).date(),county_id=county['id'])
            file_name = county['name']+'_Aggrigated_Inventory_'+timezone.now().strftime("%Y-%m-%d_%H:%M:%S_%Z")+'.csv'
            if qs.count()>0:
                fields = qs[:1].values()[0].keys()
                writer.writerow(fields)
                writer.writerows(qs.values_list(*fields))
                f.seek(0)
                upload_file_stream(settings.INVENTORY_CSV_UPLOAD_FOLDER_ID, f, file_name)
        
        
        
    
