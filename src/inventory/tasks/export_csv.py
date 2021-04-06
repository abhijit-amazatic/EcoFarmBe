import datetime
import pytz
import io
import csv

from django.conf import settings
from django.utils import timezone

from celery.task import periodic_task
from celery.schedules import crontab

from integration.box import (upload_file_stream, )
from integration.inventory import (get_inventory_summary,)

from ..models import (
    Inventory,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
)



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
    summary = get_inventory_summary(queryset, statuses=None)
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
        'trim_quantity':summary['trim_quantity'],
        'average_thc':summary['average_thc']
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
        summary = get_inventory_summary(queryset, statuses=None)
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
            'trim_quantity':summary['trim_quantity'],
            'average_thc':summary['average_thc']
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

