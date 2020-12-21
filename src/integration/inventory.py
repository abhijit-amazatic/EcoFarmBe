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
    INVENTORY_BOX_ID,
    INVENTORY_TAXES,
)
from pyzoho.inventory import Inventory
from .models import (Integration, )
from labtest.models import (LabTest, )
from inventory.models import PriceChange, Inventory as InventoryModel, Documents
from cultivar.models import (Cultivar, )
from integration.crm import (get_labtest, search_query,)
from integration.box import (upload_file_stream, create_folder,
                             get_preview_url, update_file_version,
                             get_thumbnail_url, get_inventory_folder_id)


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
    inventory = Inventory(
        client_id=INVENTORY_CLIENT_ID,
        client_secret=INVENTORY_CLIENT_SECRET,
        refresh_token=refresh_token,
        redirect_uri=INVENTORY_REDIRECT_URI,
        organization_id=INVENTORY_ORGANIZATION_ID,
        access_token=access_token,
        access_expiry=access_expiry
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
    for name in ['inventory_efd', 'inventory_efl']:
        inventory = get_inventory_obj(name)
        item = inventory.get_inventory(item_id=item_id)
        if item.get('item_id'):
            return name

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
    if not isinstance(INVENTORY_TAXES, dict):
        taxes = json.loads(INVENTORY_TAXES)
    else:
        taxes = INVENTORY_TAXES
    if 'Flower' in record['category_name']:
        return record['price'] - taxes['Flower']
    elif 'Trim' in record['category_name']:
        return record['price'] - taxes['Trim']

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
                    except Exception:
                        link = get_preview_url(new_file)
                    response.append(link)
            return response
        return response
    except Exception as exc:
        print(exc)

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
            'Tops', 'Tops - THC', 'Smalls','In the Field',
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

def get_county(vendor_name):
    """
    Get county grown for inventory item.
    """
    try:
        response = search_query('Vendors', vendor_name, 'Vendor_Name', True)
        if response.get('status_code') == 200:
            return response.get('response')[0].get('County')
        return None
    except Exception:
        return None

def get_inventory_name(inventory_name):
    """
    Return inventory name
    """
    if 'efl' in inventory_name:
        return 'EFL'
    return 'EFD'

def fetch_inventory_from_list(inventory_name, inventory_list):
    """
    Fetch list of inventory from Zoho Inventory.
    """
    cultivar = None
    for record in inventory_list:
        record = get_inventory_item(inventory_name=inventory_name, item_id=record)
        try:
            record['pre_tax_price'] = get_pre_tax_price(record)
            cultivar = get_cultivar_from_db(record['cf_strain_name'])
            if cultivar:
                record['cultivar'] = cultivar
            labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
            if labtest:
                record['labtest'] = labtest
            documents = check_documents(inventory_name, record)
            if documents and len(documents) > 0:
                record['documents'] = documents
            if record['cf_vendor_name']:
                record['county_grown'] = get_county(record['cf_vendor_name'])
            if record['category_name']:
                record['parent_category_name'] = get_parent_category(record['category_name'])
            record['inventory_name'] = get_inventory_name(inventory_name)
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
                record['pre_tax_price'] = get_pre_tax_price(record)
                cultivar = get_cultivar_from_db(record['cf_strain_name'])
                if cultivar:
                    record['cultivar'] = cultivar
                labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
                if labtest:
                    record['labtest'] = labtest
                documents = check_documents(inventory_name, record)
                if documents and len(documents) > 0:
                    record['documents'] = documents
                if record['cf_vendor_name']:
                    record['county_grown'] = get_county(record['cf_vendor_name'])
                if record['category_name']:
                    record['parent_category_name'] = get_parent_category(record['category_name'])
                record['inventory_name'] = get_inventory_name(inventory_name)
                obj = InventoryModel.objects.update_or_create(
                    item_id=record['item_id'],
                    defaults=record)
                # update_price_change(price_data, record)
            except Exception as exc:
                import traceback
                traceback.print_exc()
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
        record['pre_tax_price'] = get_pre_tax_price(record)
        # try:
        #     item = InventoryModel.objects.get(item_id=record['item_id'])
        #     price_data[record['item_id']] = item.price
        # except InventoryModel.DoesNotExist:
        #     price_data[record['item_id']] = 0
        cultivar = get_cultivar_from_db(record['cf_strain_name'])
        if cultivar:
            record['cultivar'] = cultivar
        labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
        if labtest:
            record['labtest'] = labtest
        documents = check_documents(inventory_name, record)
        if documents and len(documents) > 0:
            record['documents'] = documents
        if record['cf_vendor_name']:
            record['county_grown'] = get_county(record['cf_vendor_name'])
        if record['category_name']:
            record['parent_category_record'] = get_parent_category(record['category_name'])
        record['inventory_name'] = get_inventory_name(inventory_name)
        obj, created = InventoryModel.objects.update_or_create(
            item_id=record['item_id'],
            defaults=record)
        # update_price_change(price_data, record)
        return obj.item_id
    except Exception as exc:
        print(exc)
        return {}

def update_inventory_thumbnail():
    """
    Update  inventory thumbnail urls.
    """
    inventory = Documents.objects.filter(
        status='AVAILABLE',
        file_type__in=['image/jpeg', 'image/png'],
        thumbnail_url=None)
    for item in inventory:
        folder_id = get_inventory_folder_id(item.sku)
        url = get_thumbnail_url(item.box_id, folder_id, item.name)
        inv = Inventory.objects.get(item_id=item.object_id)
        item.thumbnail_url = url
        inv.thumbnail_url = url
        item.save()
        inv.save()
    return inventory