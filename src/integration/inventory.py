import json
from logging import error
import operator
from functools import reduce
from datetime import (datetime, timedelta)
from io import BytesIO
from urllib.parse import (unquote, )
from PIL import Image
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
    INVENTORY_IMAGE_CROP_RATIO,
)
from django.db.models import (Sum, F, Min, Max, Avg, Q, Func, ExpressionWrapper, DateField,)
from django.utils import  timezone
from pyzoho.inventory import Inventory
from .models import (Integration, )
from brand.models import License
from .inventory_data import(INVENTORY_ITEM_CATEGORY_NAME_ID_MAP, )
from labtest.models import (LabTest, )
from inventory.models import PriceChange, Inventory as InventoryModel, Documents
from cultivar.models import (Cultivar, )
from integration.crm import (get_labtest, search_query, get_record, )
from inventory.utils import (get_item_tax, )
from integration.apps.aws import (upload_compressed_file_stream_to_s3, )
from integration.box import (upload_file_stream, create_folder,
                             get_preview_url, update_file_version,
                             get_thumbnail_url, get_inventory_folder_id,
                             get_file_from_link, get_thumbnail_url, get_folder_items,
                             get_file_information, )
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

def get_vendor_id(inventory_obj, vendor_name):
    """
    Get vendor id from zoho.
    """
    vendor_id = None
    resp = inventory_obj.get_contact(params={'contact_name': vendor_name, 'contact_type': 'vendor'})
    if resp.get('code') == 0:
        for vendor in resp.get('contacts'):
            if vendor.get('contact_name', '') == vendor_name:
                if vendor.get('contact_type') == 'vendor':
                    vendor_id = vendor.get('contact_id')
                    break
    return vendor_id

def get_vendor_id_by_client_id(inventory_obj, client_id):
    """
    Get vendor id from zoho using client id.
    """
    # client_id = str(client_id)
    vendor_id = None
    resp = inventory_obj.get_contact(params={'cf_client_id': client_id, 'contact_type': 'vendor'})
    if resp.get('code') == 0:
        for vendor in resp.get('contacts'):
            if vendor.get('custom_field_hash', {}).get('cf_client_id', '') == str(client_id):
                if vendor.get('contact_type') == 'vendor':
                    vendor_id = vendor.get('contact_id')
                    break
    return vendor_id


def get_user_id(inventory, email):
    """
    Get vendor id from zoho.
    """
    result = inventory.get_user(params={'email': email})
    if result.get('code') == 0:
        for user in result.get('users'):
            if user.get('email') == email:
                return user.get('user_id')

def get_item_category_id(inv_obj, category_name, metadata={}):
    cat_id = ''
    if not metadata:
        resp_metadata = inv_obj.get_metadata(params={})
        if resp_metadata.get('code') == 0:
            metadata = resp_metadata
    if isinstance(metadata, dict) and metadata.get('categories'):
        categories = metadata.get('categories')
        for category in categories:
            if category.get('name') == category_name:
                cat_id = category.get('category_id')
    if not cat_id:
        org_id = inv_obj.ORGANIZATION_ID
        cat_id = INVENTORY_ITEM_CATEGORY_NAME_ID_MAP.get(org_id, {}).get(category_name, '')
    return cat_id

def create_inventory_item(inventory_name, record, params={}):
    """
    Create an inventory item in zoho inventory.
    """
    inventory = get_inventory_obj(inventory_name)

    if record.get('cf_vendor_name'):
        try:
            int(record.get('cf_vendor_name'))
        except ValueError:
            vendor_id = get_vendor_id(inventory, record.get('cf_vendor_name'))
            if not vendor_id:
                return {"code": 1003, "message": f"Vendor \'{record.get('cf_vendor_name')}\' not in zoho books."}
            else:
                record['cf_vendor_name'] = vendor_id
    # else:
    #     return {"code": 1003, "message": f"cf_vendor_name is required."}

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

    if record.get('cf_vendor_name'):
        try:
            int(record.get('cf_vendor_name'))
        except ValueError:
            vendor_id = get_vendor_id(inventory, record.get('cf_vendor_name'))
            if not vendor_id:
                return {"code": 1003, "message": f"Vendor \'{record.get('cf_vendor_name')}\' not in zoho books."}
            else:
                record['cf_vendor_name'] = vendor_id

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

def get_composite_item(inventory_name, item_id=None, params={}):
    """
    Get composite inventory item.
    """
    inventory = get_inventory_obj(inventory_name)
    return inventory.get_composite_inventory(item_id=item_id)

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

def get_packages(inventory_name, package_id=None, params={}):
    """
    Return packages.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.Package()
    return obj.get_package(package_id=package_id, params=params)

def create_package(inventory_name, record, params={}):
    """
    Create packages.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.Package()
    return obj.create_package(record=record, params=params)

def update_package(inventory_name, package_id, record, params={}):
    """
    Update packages.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.Package()
    return obj.update_package(package_id=package_id, record=record, params=params)

def get_sales_returns(inventory_name, sales_return_id=None, params={}):
    """
    Return packages.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.SalesReturn()
    return obj.get_sales_return(sales_return_id=sales_return_id, params=params)

def create_sales_return(inventory_name, record, params={}):
    """
    Create sales return.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.SalesReturn()
    return obj.create_sales_return(record=record, params=params)

def update_sales_return(inventory_name, sales_return_id, record, params={}):
    """
    Update sales return.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.SalesReturn()
    return obj.update_sales_return(sales_return_id=sales_return_id, record=record, params=params)

def get_contacts(inventory_name, contact_id=None, params={}):
    """
    Return a contacts or list of contacts.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.Contact()
    return obj.get_contacts(contact_id=contact_id, params=params)

def create_contact(inventory_name, record, params={}):
    """
    Create contact.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.Contact()
    return obj.create_contact(record=record, params=params)

def update_contact(inventory_name, contact_id, record, params={}):
    """
    Update contact.
    """
    inventory = get_inventory_obj(inventory_name)
    obj = inventory.Contact()
    return obj.update_contact(contact_id=contact_id, record=record, params=params)

def get_inventory_metadata(inventory_name, params={}):
    """
    Return inventory meta data.
    """
    inventory = get_inventory_obj(inventory_name)
    return inventory.get_metadata(params=params)

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

def get_books_name_from_inventory_name(inventory_name):
    """
    Return books organization name from inventory organization name.
    """
    books_names = {
        'inventory_efl': 'books_efl',
        'inventory_efd': 'books_efd',
        'inventory_efn': 'books_efn',
    }
    return books_names[inventory_name]

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
    # taxes = TaxVariable.objects.values('cultivar_tax','trim_tax')[0]
    # if 'Flower' in record['category_name']:
    #     return record['price'] - float(taxes['cultivar_tax'])
    # elif 'Trim' in record['category_name']:
    #     return record['price'] - float(taxes['trim_tax'])
    tax = get_item_tax(
        record.get('category_name'),
        trim_used=float(record.get('cf_trim_qty_lbs')) if record.get('cf_trim_qty_lbs') else None,
        item_quantity=float(record.get('cf_batch_qty_g')) if record.get('cf_batch_qty_g') else None ,
    )
    if isinstance(tax, float):
        return record['price'] - tax
    # Issue:- It will call Books API multiple times.
    # taxes = get_tax_rates()
    # if 'Flower' in record['category_name']:
    #     return record['price'] - taxes[ESTIMATE_TAXES['Flower']]
    # elif 'Trim' in record['category_name']:
    #     return record['price'] - taxes[ESTIMATE_TAXES['Trim']]

def crop_image_to_aspect_ratio(compressed_file):
    crop_x = 0
    crop_y = 0

    img = Image.open(compressed_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    o_width, o_height = img.size
    img_ratio = round(o_width/o_height, 5)
    img_crop_ratio = round(INVENTORY_IMAGE_CROP_RATIO, 5) 
    if img_ratio != img_crop_ratio:
        if img_ratio < img_crop_ratio:
            n_width = o_width
            n_height = int(round(o_width/INVENTORY_IMAGE_CROP_RATIO))
            crop_y = int((o_height - n_height)/2)
        elif img_ratio > img_crop_ratio:
            n_height = o_height
            n_width = int(round(o_height*INVENTORY_IMAGE_CROP_RATIO))
            crop_x = int((o_width - n_width)/2)

        cropped_img = img.crop((crop_x, crop_y, crop_x+n_width, crop_y+n_height))

        file_obj = BytesIO()
        cropped_img.save(file_obj, format='JPEG')
        return file_obj

    return compressed_file


def get_s3_mobile_url(compressed_file, folder_name, file_name):
    """
    Get mobile url for image.
    """
    resize_width=1280
    resize_height=int(round(resize_width/INVENTORY_IMAGE_CROP_RATIO))
    img = Image.open(compressed_file)
    resized_img = img.resize((resize_width, resize_height))
    file_obj = BytesIO()
    resized_img.save(file_obj, format='JPEG')
    file_name = file_name.split('.')
    file_name = file_name[0] + '-mobile.jpg'

    s3_key = '/'.join(('inventory', folder_name, file_name))
    url = upload_compressed_file_stream_to_s3(file_obj, s3_key, content_type='image/jpeg')
    return url

def get_s3_thumbnail_url(compressed_file, folder_name, file_name):
    """
    Get mobile url for image.
    """
    img = Image.open(compressed_file)
    img.thumbnail((160, 160))
    file_obj = BytesIO()
    img.save(file_obj, format='JPEG')
    file_name = file_name.split('.')
    file_name = file_name[0] + '-thumbnail.jpg'

    s3_key = '/'.join(('inventory', folder_name, file_name))
    url = upload_compressed_file_stream_to_s3(file_obj, s3_key, content_type='image/jpeg')
    return url


def check_documents(inventory_name, record):
    """
    Check if record has any documents.
    """
    try:
        response = list()
        thumbnail_url = None
        mobile_url = None
        if record.get('image_name'):
            record = get_inventory_item(inventory_name, record['item_id'])
        if record.get('documents') and len(record['documents']) > 0:
            folder_name = f"{record['sku']}"
            # folder_id = create_folder(INVENTORY_BOX_ID, folder_name)
            resp_docs = {}
            print(f"Item {record['sku']} image count: {len(record['documents'] or [])}" )
            for document in record['documents']:

                file_obj = get_inventory_document(inventory_name, record['item_id'], document['document_id'])
                file_obj = BytesIO(file_obj)
                file_name = document['file_name'].split('.')
                file_name = f"{document['document_id']}-{file_name[0]}.jpg"
                s3_key = '/'.join(('inventory', folder_name, file_name))
                cropped_file_obj = crop_image_to_aspect_ratio(file_obj)
                link = upload_compressed_file_stream_to_s3(file_obj, s3_key, content_type='image/jpeg')

                if document['attachment_order'] == 1: # Limit upload image to primary.
                    mobile_url = get_s3_mobile_url(cropped_file_obj, folder_name, file_name)
                    thumbnail_url = get_s3_thumbnail_url(cropped_file_obj, folder_name, file_name)

                # response.append(link)
                resp_docs[document['attachment_order']] = link
            response = [v for _, v in sorted(resp_docs.items())]
            return response, thumbnail_url, mobile_url
        return response, thumbnail_url, mobile_url
    except Exception as exc:
        print(exc)
        return None, None, None

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
            'Flower - Small',
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
            data['county_grown'] = response.get('response')[0].get('County2', [])
            data['appellation'] = response.get('response')[0].get('Appellation', [])
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

def fetch_inventory_from_list(inventory_name, inventory_list, is_composite=False):
    """
    Fetch list of inventory from Zoho Inventory.
    """
    cultivar = None
    for record in inventory_list:
        if is_composite:
            records = get_composite_item(inventory_name, item_id=record)
        else:
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
            documents, thumbnail_url, mobile_url = check_documents(inventory_name, record)
            record['documents'] = documents
            record['thumbnail_url'] = thumbnail_url
            record['mobile_url'] = mobile_url
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

def fetch_inventory(inventory_name, days=1, price_data=None, is_composite=False):
    """
    Fetch latest inventory from Zoho Inventory.
    """
    cultivar = None
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S-0000')
    has_more = True
    page = 0
    while has_more:
        if is_composite:
            records = get_composite_item(inventory_name)
        else:
            records = get_inventory_items(inventory_name, params={'page': page, 'last_modified_time': date})
        has_more = records['page_context']['has_more_page']
        page = records['page_context']['page'] + 1
        for record in records['items']:
            try:
                if is_composite:
                    record.update(get_composite_item(inventory_name, item_id=record['item_id']))
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
                documents, thumbnail_url, mobile_url = check_documents(inventory_name, record)
                record['documents'] = documents
                record['thumbnail_url'] = thumbnail_url
                record['mobile_url'] = mobile_url
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

def fetch_inventory_item_fields(inventory_name, fields=(), days=None, is_composite=False):
    """
    Fetch latest inventory from Zoho Inventory.
    """
    cultivar = None
    has_more = True
    page = 0

    params = {'page': page}
    if days:
        yesterday = datetime.now() - timedelta(days=days)
        date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S-0000')
        params['last_modified_time'] = date

    while has_more:
        if is_composite:
            records = get_composite_item(inventory_name)
        else:
            records = get_inventory_items(inventory_name, params=params)
        try:
            has_more = records['page_context']['has_more_page']
            params['page'] = records['page_context']['page'] + 1
        except Exception as e:
            print({'error': e, 'response': records,})
            return None
        else:
            for record in records['items']:
                try:
                    if is_composite:
                        record.update(get_composite_item(inventory_name, item_id=record['item_id']))
                    if 'pre_tax_price' in fields:
                        try:
                            record['pre_tax_price'] = get_pre_tax_price(record)
                        except KeyError:
                            pass
                    if 'cultivar' in fields:
                        try:
                            cultivar = get_cultivar_from_db(record['cf_strain_name'])
                            if cultivar:
                                record['cultivar'] = cultivar
                        except KeyError:
                            pass

                    if 'labtest' in fields:
                        try:
                            labtest = get_labtest_from_db(record['cf_lab_test_sample_id'])
                            if labtest:
                                record['labtest'] = labtest
                        except KeyError:
                            pass

                    if any(f in fields for f in ('documents', 'thumbnail_url', 'mobile_url')):
                        documents, thumbnail_url, mobile_url = check_documents(inventory_name, record)
                        record['documents'] = documents
                        record['thumbnail_url'] = thumbnail_url
                        record['mobile_url'] = mobile_url


                    if any(f in fields for f in ('county_grown', 'appellation', 'nutrients', 'ethics_and_certification')):
                        try:
                            if record['cf_vendor_name']:
                                record.update(get_record_data(record['cf_vendor_name']))
                        except KeyError:
                            pass

                    if 'parent_category_name' in fields:
                        try:
                            if record['category_name']:
                                record['parent_category_name'] = get_parent_category(record['category_name'])
                        except KeyError:
                            pass

                    record['inventory_name'] = get_inventory_name_from_db(inventory_name)
                    update_data = {k: v for k, v in record.items() if k in fields}
                    qs = InventoryModel.objects.filter(item_id=record['item_id'])
                    qs.update(**update_data)
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
        documents, thumbnail_url, mobile_url = check_documents(inventory_name, record)
        record['documents'] = documents
        record['thumbnail_url'] = thumbnail_url
        record['mobile_url'] = mobile_url
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
        print(exc)
        return {}

# def update_inventory_thumbnail():
#     """
#     Update  inventory thumbnail urls.
#     """
#     inventory = InventoryModel.objects.filter(documents__isnull=False)
#     for item in inventory:
#         folder_id = get_inventory_folder_id(item.sku)
#         file_info = get_file_from_link(item.documents[0])
#         url = get_thumbnail_url(item.box_id, folder_id, item.name)
#         inv = Inventory.objects.get(item_id=item.object_id)
#         item.thumbnail_url = url
#         inv.thumbnail_url = url
#         item.save()
#         inv.save()

def update_inventory_thumbnail():
    """
    Update  inventory thumbnail urls.
    """
    from requests import request

    inventory = InventoryModel.objects.filter(documents__isnull=False)
    for item in inventory:
        if item.documents:
            r = request('get', item.documents[0])
            if r.status_code == 200:
                url = get_s3_thumbnail_url(item.box_id, item.sku, item.name)
                item.thumbnail_url = url
                item.save()

def get_average_thc(inventory):
    """
    Ref:
    (qty*THC)+(qty*THC)+.. +/Sum(qty)
    """
    try:
        item_qs = inventory.filter(cf_cfi_published=True,status='active',actual_available_stock__gt=0,labtest__Total_THC__gt=0).select_related()
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
        categories = ['Processing',
                      'Vegging,Flowering,Under Contract', 'Sold']
        labtest = LabTest.objects.filter(id__in=inventory.values('labtest_id'))
        response['total_thc_min'] = labtest.aggregate(Min('Total_THC'))['Total_THC__min']
        response['total_thc_max'] = labtest.aggregate(Max('Total_THC'))['Total_THC__max']
        response['average_thc'] = get_average_thc(inventory)
        if statuses in categories:
            response['total_quantity'] = inventory.filter(inventory_name__in=['EFD','EFL','EFN']).aggregate(Sum('cf_quantity_estimate'))['cf_quantity_estimate__sum']
            for category in ['Tops', 'Smalls', 'Trim']:
                response[category.lower() + '_quantity'] = inventory.filter(
                    cf_cannabis_grade_and_category__contains=category).aggregate(
                        Sum('cf_quantity_estimate'))['cf_quantity_estimate__sum']
            response['total_value'] = inventory.filter().aggregate(
                    total=Sum(F('cf_quantity_estimate')*F('pre_tax_price')))['total']
        else:
            response['total_quantity'] = inventory.filter(inventory_name__in=['EFD','EFL','EFN']).aggregate(Sum('actual_available_stock'))['actual_available_stock__sum']
            for category in ['Tops', 'Smalls', 'Trim']:
                response[category.lower() + '_quantity'] = inventory.filter(
                    cf_cannabis_grade_and_category__contains=category).aggregate(
                        Sum('actual_available_stock'))['actual_available_stock__sum']
            response['total_value'] = inventory.filter().aggregate(
                    total=Sum(F('actual_available_stock')*F('pre_tax_price')))['total']
        response['average'] = inventory.aggregate(Avg('pre_tax_price'))['pre_tax_price__avg']
        response['batch_varities'] = inventory.order_by().distinct('sku').count()
        return response
    except Exception as exc:
        return {'error': f'{exc}'}
            
def get_category_count(params, filtered_qs):
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
    for name, category in categories.items():
        response[name] = filtered_qs.filter(cf_status__in=category).count()
    return response

def resize_box_images():
    """
    Resize box images.
    """
    import requests
    from PIL import Image
    from io import BytesIO

    documents = Documents.objects.filter(
        status='AVAILABLE',
        doc_type__isnull=True,
        file_type='image/jpeg'
    )
    resize_tuple = (1280, 720)
    for document in documents:
        url = get_preview_url(document.box_id)
        data = BytesIO(requests.get(url).content)
        out = BytesIO()
        img = Image.open(data)
        img.resize(resize_tuple)
        img.save(out, format='JPEG')
        file_name = document.name.split('.')
        parent = get_file_information(document.box_id)['parent'].id
        mobile_id = upload_file_stream(parent, out, file_name[0] + '-resized.' + file_name[1])
        try:
            mobile_url = get_preview_url(mobile_id.id)
        except AttributeError:
            mobile_url = get_preview_url(mobile_id)
        document.mobile_url = mobile_url
        document.save()
        try:
            item = InventoryModel.objects.get(item_id=document.object_id)
            item.mobile_url = mobile_url
            item.save()
        except Inventory.DoesNotExist:
            print('here')
            pass

def get_line_item(obj, data):
    """
    Return item from Zoho inventory.
    """
    line_items = list()
    if not data.get('line_items'):
        return {"code": 1004, "error": "line items not provided"}
    for line_item in data.get('line_items'):
        resp = obj.get_inventory(params={'search_text': line_item['sku']}, parse=False)
        if resp.get('code') == 0:
            fetched_items = resp['items']
            fetched_item = None
            for i in fetched_items:
                if i['sku'] == line_item['sku']:
                    fetched_item = i
                    break
            if not fetched_item:
                return {"code": 1003, "message": "Item not in zoho inventory."}
            item = {
                'item_id': fetched_item.get('item_id'),
                'sku': fetched_item.get('sku'),
                'name': fetched_item.get('name'),
                'rate': line_item.get('rate', fetched_item.get('rate')),
                'quantity': line_item.get('quantity'),
                'category_name': line_item.get('category_name'),
                'item_custom_fields': line_item.get('item_custom_fields'),
                'ask_price': line_item.get('ask_price'),
                'description': line_item.get('description')
            }
            if line_item.get('warehouse_id'):
                item['warehouse_id'] = line_item.get('warehouse_id')

            line_items.append(item)
        else:
            {"code": 1003, "message": "Item not found in zoho inventory."}
    data['line_items'] = line_items
    return {"code": 0, "data": data}


def create_purchase_order(inventory_name, record, params=None):
    """
    Create purchase order to Zoho books.
    """
    try:
        inv_obj = get_inventory_obj(inventory_name)
        po_obj = inv_obj.PurchaseOrders()

        if not record.get('vendor_id') and record.get('vendor_name'):
            vendor_id = get_vendor_id(inv_obj, record.get('vendor_name'))
            if not vendor_id:
                return {"code": 1003, "message": f"Vendor \'{record.get('vendor_name')}\' not in zoho books."}
            else:
                record['vendor_id'] = vendor_id

        if not record.get('vendor_id'):
            return {"code": 1003, "message": f"vendor_id is required."}

        result = get_line_item(inv_obj, record)
        if result['code'] != 0:
           return result
        return po_obj.create_purchase_order(result['data'], parameters=params)
    except Exception as exc:
        return {
            "code": 400,
            "error": exc
        }

def submit_purchase_order(inventory_name, po_id, params={}):
    """
    Submit specific purchase order.
    """
    obj = get_inventory_obj(inventory_name)
    po_obj = obj.PurchaseOrders()
    return po_obj.submit_purchase_order(po_id=po_id, parameters=params)
