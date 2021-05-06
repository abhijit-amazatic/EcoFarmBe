import json
from datetime import (datetime, timedelta)
from io import BytesIO
from urllib.parse import (unquote, )
from core.settings import (
    INVENTORY_CLIENT_ID,
    INVENTORY_CLIENT_SECRET,
    INVENTORY_REFRESH_TOKEN,
    INVENTORY_REDIRECT_URI,
    INVENTORY_EFL_ORGANIZATION_ID,
    INVENTORY_EFD_ORGANIZATION_ID,
    INVENTORY_EFN_ORGANIZATION_ID,
    INVENTORY_BOX_ID,
    INVENTORY_TAXES,
)
from django.db.models import (Sum, F, Min, Max, Avg, Q)
from pyzoho.inventory import Inventory
from .models import (Integration, )
from labtest.models import (LabTest, )
from inventory.models import PriceChange, Inventory as InventoryModel, Documents
from cultivar.models import (Cultivar, )
from integration.crm import (get_labtest, search_query, get_record, )
from integration.box import (upload_file_stream, create_folder,
                             get_preview_url, update_file_version,
                             get_thumbnail_url, get_inventory_folder_id,
                             get_file_from_link, get_thumbnail_url, get_folder_items,)
from fee_variable.models import *


def get_inventory_obj(inventory_name):
    """
    Return pyzoho.inventory object.
    """
    try:
        token = Integration.objects.get(name=inventory_name)
        access_token = token.access_token
        access_expiry = token.access_expiry
        refresh_token = token.refresh_token
    except Integration.DoesNotExist:
        access_token = access_expiry = None
        refresh_token = INVENTORY_REFRESH_TOKEN
    if inventory_name == 'inventory_efd':
        INVENTORY_ORGANIZATION_ID = INVENTORY_EFD_ORGANIZATION_ID
    elif inventory_name == 'inventory_efl':
        INVENTORY_ORGANIZATION_ID = INVENTORY_EFL_ORGANIZATION_ID
    elif inventory_name == 'inventory_efn':
        INVENTORY_ORGANIZATION_ID = INVENTORY_EFN_ORGANIZATION_ID
    inventory = Inventory(
        client_id=INVENTORY_CLIENT_ID,
        client_secret=INVENTORY_CLIENT_SECRET,
        refresh_token=refresh_token,
        redirect_uri=INVENTORY_REDIRECT_URI,
        organization_id=INVENTORY_ORGANIZATION_ID,
        access_token=access_token,
        access_expiry=access_expiry,
        inventory_name=inventory_name
    )
    if inventory.refreshed:
        Integration.objects.update_or_create(
            name=inventory_name,
            defaults={
                "name": inventory_name,
                "client_id":inventory.CLIENT_ID,
                "client_secret":inventory.CLIENT_SECRET,
                "access_token":inventory.ACCESS_TOKEN,
                "access_expiry":inventory.ACCESS_EXPIRY[0],
                "refresh_token":inventory.REFRESH_TOKEN
                }
        )
    return inventory

def get_vendor_id(inventory, record):
    """
    Get vendor id from zoho.
    """
    vendor_name = inventory.get_contact(params={'contact_name': record.get('cf_vendor_name')})
    if vendor_name.get('code') == 0:
        for vendor in vendor_name.get('contacts'):
            if vendor.get('vendor_name') == record.get('cf_vendor_name') and vendor.get('contact_type') == 'vendor':
                return vendor.get('contact_id')

def get_user_id(inventory, email):
    """
    Get vendor id from zoho.
    """
    result = inventory.get_user(params={'email': email})
    if result.get('code') == 0:
        for user in result.get('users'):
            if user.get('email') == email:
                return user.get('user_id')


def create_inventory_item(inventory_name, record, params={}):
    """
    Create an inventory item in zoho inventory.
    """
    inventory = get_inventory_obj(inventory_name)
    if 'cf_vendor_name' in record:
        vendor_id = get_vendor_id(inventory, record)
        if vendor_id:
            record['cf_vendor_name'] = vendor_id
        else:
            record.pop('cf_vendor_name')

    if 'cf_procurement_rep' in record:
        user_id = get_user_id(inventory, record['cf_procurement_rep'])
        if user_id:
            record['cf_procurement_rep'] = user_id
        else:
            record.pop('cf_procurement_rep')

    return inventory.create_item(record, params=params)

def update_inventory_item(inventory_name, record_id, record, params={}):
    """
    Update an inventory item in zoho inventory.
    """
    inventory = get_inventory_obj(inventory_name)
    if 'cf_vendor_name' in record:
        vendor_id = get_vendor_id(inventory, record)
        if vendor_id:
            record['cf_vendor_name'] = vendor_id
        else:
            record.pop('cf_vendor_name')
    if 'cf_procurement_rep' in record:
        user_id = get_user_id(inventory, record['cf_procurement_rep'])
        if user_id:
            record['cf_procurement_rep'] = user_id
        else:
            record.pop('cf_procurement_rep')
    return inventory.update_item(record_id, record, params=params)

def get_inventory_items(inventory_name, params={}):
    """
    Return Inventory list.
    """
    inventory = get_inventory_obj(inventory_name)
    return inventory.get_inventory(params=params)

def get_inventory_item(inventory_name, item_id):
    """
    Return inventory item.
    """
    inventory = get_inventory_obj(inventory_name)
    return inventory.get_inventory(item_id=item_id)

def get_inventory_document(inventory_name, item_id, document_id, params={}):
    """
    Return documents for inventory item.
    """
    inventory = get_inventory_obj(inventory_name)
    return inventory.get_item_documents(item_id, document_id, params=params)

def upload_inventory_document(inventory_name, item_id, files, params={}):
    """
    Upload inventory document.
    """
    inventory = get_inventory_obj(inventory_name)
    return inventory.upload_item_document(item_id, files, params=params)

def get_inventory_name(item_id):
    """
    Get inventory name.
    """
    item = InventoryModel.objects.get(item_id=item_id)
    inventory_names = {
        'EFL': 'inventory_efl',
        'EFD': 'inventory_efd',
        'EFN': 'inventory_efn',
    }
    return inventory_names[item.inventory_name]

def get_cultivar_from_db(cultivar_name):
    """
    Return cultivar from db.
    """
    try:
        cultivar = Cultivar.objects.filter(cultivar_name=cultivar_name)
        return cultivar.first()
    except Cultivar.DoesNotExist:
        return None

def get_labtest_from_db(labtest_sample_id):
    """
    Return labtest from db.
    """
    try:
        if labtest_sample_id:
            labtest = LabTest.objects.filter(Sample_I_D=labtest_sample_id)
            return labtest.first()
        return None
    except LabTest.DoesNotExist as exc:
        print(exc)
        return None

def get_vendor_from_crm(vendor_name):
    """
    Get inventory vendor from crm.
    """
    vendors = search_query(
        'Vendors',
        vendor_name,
        'Vendor_Name'
    )
    if vendors['status_code'] == 200:
        return vendors.get('response')[0]
    return {}

def get_pre_tax_price(record):
    """
    Get pre tax price.
    """
    taxes = TaxVariable.objects.values('cultivar_tax','trim_tax')[0]
    if 'Flower' in record['category_name']:
        return record['price'] - float(taxes['cultivar_tax'])
    elif 'Trim' in record['category_name']:
        return record['price'] - float(taxes['trim_tax'])

    # Issue:- It will call Books API multiple times.
    # taxes = get_tax_rates()
    # if 'Flower' in record['category_name']:
    #     return record['price'] - taxes[ESTIMATE_TAXES['Flower']]
    # elif 'Trim' in record['category_name']:
    #     return record['price'] - taxes[ESTIMATE_TAXES['Trim']]

def check_documents(inventory_name, record):
    """
    Check if record has any documents.
    """
    try:
        response = list()
        thumbnail_url = None
        if record.get('image_name'):
            record = get_inventory_item(inventory_name, record['item_id'])
        if record.get('documents') and len(record['documents']) > 0:
            folder_name = f"{record['sku']}"
            folder_id = create_folder(INVENTORY_BOX_ID, folder_name)
            for document in record['documents']:
                if document['attachment_order'] == 1: # Limit upload image to primary.
                    file_obj = get_inventory_document(inventory_name, record['item_id'], document['document_id'])
                    file_obj = BytesIO(file_obj)
                    file_name = f"{document['document_id']}-{document['file_name']}"
                    new_file = upload_file_stream(folder_id, file_obj, file_name)
                    try:
                        link = get_preview_url(new_file.id)
                        thumbnail_url = get_thumbnail_url(new_file.id, folder_id, file_name)
                    except Exception:
                        link = get_preview_url(new_file)
                        thumbnail_url = get_thumbnail_url(new_file, folder_id, file_name)
                    response.append(link)
            return response, thumbnail_url
        return response, thumbnail_url
    except Exception as exc:
        print(exc)
        return None, None

def upload_file_to_box(item_name, item_id, file_obj):
    """
    Upload image/video file to box.
    """
    folder_name = f"{item_name}-{item_id}"
    folder_id = create_folder(INVENTORY_BOX_ID, folder_name)
    try:
        file_name = file_obj.name.split('/')[-1]
    except Exception:
        file_name = file_obj.name
    new_file = upload_file_stream(folder_id, file_obj, file_name)
    try:
        return get_preview_url(new_file.id)
    except Exception:
        return get_preview_url(new_file)

def get_price_change(old_price, new_price):
    """
    Return price change.
    """
    return round(((new_price - old_price)/old_price)*100, 2)
    
def update_price_change(price_data, record):
    """
    Update new price in db.
    """
    price_change_array = dict()
    item_id = record['item_id']
    if price_data.get(item_id):
        old_price = price_data.get(item_id)
        new_price = record['price']
        price_change = get_price_change(old_price, new_price)
        price_change_array['date'] = datetime.now().isoformat()
        price_change_array['price'] = price_change    
        try:
            pc = PriceChange.objects.get(item_id=item_id)
            array = pc.price_array
            array.append(price_change_array)
            pc.price_array = array
            pc.save()
        except PriceChange.DoesNotExist as exc:
            print('exception', exc)
            PriceChange.objects.create(
                item_id=item_id,
                price_array=[price_change_array],
            )
        item = InventoryModel.objects.get(item_id=item_id)
        item.current_price_change = price_change
        item.save()
    return True

def get_parent_category(category_name):
    """
    Return parent category name.
    """
    category_dict = {
        'Wholesale - Flower': [
            'Tops', 'Tops - THC', 'Smalls', 'In the Field',
            'Flower - Tops',
            'Flower - Bucked Untrimmed',
            'Flower - Bucked Untrimmed - Seeded',
            'Flower - Bucked Untrimmed - Contaminated'],
        'Wholesale - Trim': ['Trim - THC', 'Trim - CBD', 'Trim'],
        'Bucked Untrimmed': ['Bucked Untrimmed'],
        'Wholesale - Concentrates': [
            'Crude Oil',
            'Crude Oil - THC',
            'Crude Oil - CBD',
            'Distillate Oil',
            'Distillate Oil - THC',
            'Distillate Oil - THC - First Pass',
            'Distillate Oil - THC - Second Pass',
            'Distillate Oil - CBD',
            'Shatter',
            'Sauce',
            'Crumbe',
            'Crumble',
            'Kief',
            'Hash'],
        'Waste': ['Distillate Waste'],
        'Lab Testing': ['Lab Testing'],
        'Wholesale - Terpenes': ['Terpenes - Cultivar Specific', 'Terpenes - Cultivar Blended'],
        'Wholesale - Isolates': [
            'Isolates - CBD',
            'Isolates - THC',
            'Isolates - CBG',
            'Isolates - CBN'],
        'Services': ['QC', 'Transport', 'Secure Cash Handling', 'Services'],
        'Packaged Goods': ['Packaged Goods'],}
    for k, v in category_dict.items():
        if category_name in v:
            return k
    if category_name in category_dict.keys():
        return category_name
    return None

def get_from_licenses(response, field):
    """
    Get data from license module.
    """
    vendor = response.get('response')[0].get('Vendor_Name')
    data = search_query('Vendors_X_Licenses', vendor, 'Licenses_Module', True)
    if data.get('status_code') == 200:
        license_id = data.get('response')[0].get('Licenses').get('id')
        result = get_record('Licenses', license_id)
        if result.get('status_code') == 200:
            return result.get('response')[license_id].get(field)

def get_record_data(vendor_name):
    """
    Get record data for inventory item from crm.
    """
    try:
        data = dict()
        response = search_query('Vendors', vendor_name, 'Vendor_Name', True)
        if response.get('status_code') == 200:
            data['county_grown'] = response.get('response')[0].get('County')
            data['nutrients'] = get_from_licenses(response, 'Types_of_Nutrients')
            data['ethics_and_certification'] = response.get('response')[0].get('Special_Certifications')
            return data
        return {}
    except Exception as exc:
        print(exc)
        return {}

def get_inventory_name_from_db(inventory_name):
    """
    Return inventory name
    """
    if 'efl' in inventory_name:
        return 'EFL'
    elif 'efd' in inventory_name:
        return 'EFD'
    elif 'efn' in inventory_name:
        return 'EFN'

def fetch_inventory_from_list(inventory_name, inventory_list):
    """
    Fetch list of inventory from Zoho Inventory.
    """
    cultivar = None
    for record in inventory_list:
        record = get_inventory_item(inventory_name=inventory_name, item_id=record)
        try:
            try:
                record['pre_tax_price'] = get_pre_tax_price(record)
            except KeyError:
                pass
            try:
                cultivar = get_cultivar_from_db(record['cf_strain_name'])
                if cultivar:
                    record['cultivar'] = cultivar
            except KeyError:
                pass
            try:
                labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
                if labtest:
                    record['labtest'] = labtest
            except KeyError:
                pass
            documents, thumbnail_url = check_documents(inventory_name, record)
            record['documents'] = documents
            record['thumbnail_url'] = thumbnail_url
            try:
                if record['cf_vendor_name']:
                    record.update(get_record_data(record['cf_vendor_name']))
            except KeyError:
                pass
            try:
                if record['category_name']:
                    record['parent_category_name'] = get_parent_category(record['category_name'])
            except KeyError:
                pass
            record['inventory_name'] = get_inventory_name_from_db(inventory_name)
            obj = InventoryModel.objects.update_or_create(
                item_id=record['item_id'],
                defaults=record)
        except Exception as exc:
            print({
                'item_id': record['item_id'],
                'error': exc
                })
            continue

def fetch_inventory(inventory_name, days=1, price_data=None):
    """
    Fetch latest inventory from Zoho Inventory.
    """
    cultivar = None
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S-0000')
    has_more = True
    page = 0
    while has_more:
        records = get_inventory_items(inventory_name, params={'page': page, 'last_modified_time': date})
        has_more = records['page_context']['has_more_page']
        page = records['page_context']['page'] + 1
        for record in records['items']:
            try:
                try:
                    record['pre_tax_price'] = get_pre_tax_price(record)
                except KeyError:
                    pass
                try:
                    cultivar = get_cultivar_from_db(record['cf_strain_name'])
                    if cultivar:
                        record['cultivar'] = cultivar
                except KeyError:
                    pass
                try:
                    labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
                    if labtest:
                        record['labtest'] = labtest
                except KeyError:
                    pass
                documents, thumbnail_url = check_documents(inventory_name, record)
                record['documents'] = documents
                record['thumbnail_url'] = thumbnail_url
                try:
                    if record['cf_vendor_name']:
                        record.update(get_record_data(record['cf_vendor_name']))
                except KeyError:
                    pass
                try:
                    if record['category_name']:
                        record['parent_category_name'] = get_parent_category(record['category_name'])
                except KeyError:
                    pass
                record['inventory_name'] = get_inventory_name_from_db(inventory_name)
                obj = InventoryModel.objects.update_or_create(
                    item_id=record['item_id'],
                    defaults=record)
                # update_price_change(price_data, record)
            except Exception as exc:
                print({
                    'item_id': record['item_id'],
                    'error': exc
                    })
                continue

def sync_inventory(inventory_name, response):
    """
    Webhook for Zoho inventory to sync inventory real time.
    """
    price_data = {}
    inventory = get_inventory_obj(inventory_name)
    record = json.loads(unquote(response))['item']
    record = inventory.parse_item(response=record, is_detail=True)
    try:
        try:
            record['pre_tax_price'] = get_pre_tax_price(record)
        except KeyError:
            pass
        # try:
        #     item = InventoryModel.objects.get(item_id=record['item_id'])
        #     price_data[record['item_id']] = item.price
        # except InventoryModel.DoesNotExist:
        #     price_data[record['item_id']] = 0
        try:
            cultivar = get_cultivar_from_db(record['cf_strain_name'])
            if cultivar:
                record['cultivar'] = cultivar
        except KeyError:
            pass
        try:
            labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
            if labtest:
                record['labtest'] = labtest
        except KeyError:
            pass
        documents, thumbnail_url = check_documents(inventory_name, record)
        record['documents'] = documents
        record['thumbnail_url'] = thumbnail_url
        try:
            if record['cf_vendor_name']:
                record.update(get_record_data(record['cf_vendor_name']))
        except KeyError:
            pass
        try:
            if record['category_name']:
                record['parent_category_name'] = get_parent_category(record['category_name'])
        except KeyError:
            pass
        record['inventory_name'] = get_inventory_name_from_db(inventory_name)
        obj, created = InventoryModel.objects.update_or_create(
            item_id=record['item_id'],
            defaults=record)
        # update_price_change(price_data, record)
        return obj.item_id
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(exc)
        return {}

def update_inventory_thumbnail():
    """
    Update  inventory thumbnail urls.
    """
    inventory = InventoryModel.objects.filter(documents__isnull=False)
    for item in inventory:
        folder_id = get_inventory_folder_id(item.sku)
        file_info = get_file_from_link(item.documents[0])
        url = get_thumbnail_url(item.box_id, folder_id, item.name)
        inv = Inventory.objects.get(item_id=item.object_id)
        item.thumbnail_url = url
        inv.thumbnail_url = url
        item.save()
        inv.save()
    return documents


def get_average_thc(inventory):
    """
    Ref:
    (qty*THC)+(qty*THC)+.. +/Sum(qty)
    """
    try:
        item_qs = inventory.filter(cf_cfi_published=True,actual_available_stock__gt=0,cf_status__in=['Under Contract','Available'],labtest__Total_THC__gt=0).select_related()
        summation = item_qs.aggregate(total=Sum(F('actual_available_stock') * F('labtest__Total_THC')))['total']
        quantity_sum = item_qs.aggregate(Sum('actual_available_stock'))['actual_available_stock__sum']
        avg_thc = (summation)/(quantity_sum)
        return avg_thc
    except Exception as e:
        print('exception while calculating avg thc', e)
        return 0
    
def get_inventory_summary(inventory, statuses):
    """
    Return inventory summary
    """
    try:
        response = dict()
        categories = ['In-Testing',
                      'Processing',
                      'Vegging,Flowering,Under Contract', 'Sold']
        labtest = LabTest.objects.filter(id__in=inventory.values('labtest_id'))
        response['total_thc_min'] = labtest.aggregate(Min('Total_THC'))['Total_THC__min']
        response['total_thc_max'] = labtest.aggregate(Max('Total_THC'))['Total_THC__max']
        response['average_thc'] = get_average_thc(inventory)
        if statuses in categories:
            response['total_quantity'] = inventory.filter(inventory_name='EFD').aggregate(Sum('cf_quantity_estimate'))['cf_quantity_estimate__sum']
            for category in ['Tops', 'Smalls', 'Trim']:
                response[category.lower() + '_quantity'] = inventory.filter(
                    cf_cannabis_grade_and_category__contains=category).aggregate(
                        Sum('cf_quantity_estimate'))['cf_quantity_estimate__sum']
            response['total_value'] = inventory.filter(
                category_name__contains='Flower').aggregate(
                    total=Sum(F('cf_quantity_estimate')*F('pre_tax_price')))['total']
        else:
            response['total_quantity'] = inventory.filter(inventory_name='EFD').aggregate(Sum('actual_available_stock'))['actual_available_stock__sum']
            for category in ['Tops', 'Smalls', 'Trim']:
                response[category.lower() + '_quantity'] = inventory.filter(
                    cf_cannabis_grade_and_category__contains=category).aggregate(
                        Sum('actual_available_stock'))['actual_available_stock__sum']
            response['total_value'] = inventory.filter(
                category_name__contains='Flower').aggregate(
                    total=Sum(F('actual_available_stock')*F('pre_tax_price')))['total']
        response['average'] = inventory.aggregate(Avg('pre_tax_price'))['pre_tax_price__avg']
        response['batch_varities'] = inventory.order_by().distinct('sku').count()
        return response
    except Exception as exc:
        return {'error': f'{exc}'}

def get_updated_params(params):
    """
    Update params if Array fields are present.
    """
    db_array_fields = ['ethics_and_certification', 'nutrients']
    for i in db_array_fields:
        if i in params.keys():
            val = params[i].split(',')
            params[i+'__overlap'] = params.pop(i)
            params[i+'__overlap'] = val
    return params        
    
def get_category_count(params):
    """
    Return category count.
    """
    response = dict()
    categories = {
        'Available': ('Available',),
        'Pending_Sale': ('Pending Sale',),
        'In_Testing': ('In-Testing',),
        'Processing': ('Processing',),
        'Future_Exchange': ('Vegging', 'Flowering', 'Under Contract',),
        'Market_Intelligence': ('Sold',)
    }
    params['cf_cfi_published'] = True
    updated_params = get_updated_params(params)
    inventory = InventoryModel.objects.filter(**updated_params)
    for name, category in categories.items():
        response[name] = inventory.filter(cf_status__in=category).count()
    return response

def resize_box_images():
    """
    Resize box images.
    """
    import requests
    from PIL import Image
    from io import BytesIO

    main_dir = get_folder_items(INVENTORY_BOX_ID)
    resize_tuple = (640, 480)
    for id, name in main_dir.items():
        files = get_folder_items(id)
        for file_id, file_name in files.items():
            url = get_preview_url(file_id)
            data = BytesIO(requests.get(url).content)
            out = BytesIO()
            img = Image.open(data)
            img.resize(resize_tuple)
            img.save(out, format='JPEG')
            file_name = file_name.split('.')[0]
            upload_file_stream(id, out, file_name + '-resized.jpg')
