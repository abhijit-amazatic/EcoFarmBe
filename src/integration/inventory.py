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
)
from pyzoho.inventory import Inventory
from .models import (Integration, )
from labtest.models import (LabTest, )
from inventory.models import Inventory as InventoryModel
from cultivar.models import (Cultivar, )
from integration.crm import (get_labtest, )
from integration.box import (upload_file_stream, create_folder,
                             get_preview_url, update_file_version)


def get_inventory_obj(inventory_name):
    """
    Return pyzoho.inventory object.
    """
    try:
        token = Integration.objects.get(name=inventory_name)
        access_token = token.access_token
        access_expiry = token.access_expiry
    except Integration.DoesNotExist:
        access_token = access_expiry = None
    if inventory_name == 'inventory_efd':
        INVENTORY_ORGANIZATION_ID = INVENTORY_EFD_ORGANIZATION_ID
    elif inventory_name == 'inventory_efl':
        INVENTORY_ORGANIZATION_ID = INVENTORY_EFL_ORGANIZATION_ID
    inventory = Inventory(
        client_id=INVENTORY_CLIENT_ID,
        client_secret=INVENTORY_CLIENT_SECRET,
        refresh_token=INVENTORY_REFRESH_TOKEN,
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

def get_cultivar_from_db(cultivar_name):
    """
    Return cultivar from db.
    """
    try:
        cultivar = Cultivar.objects.filter(cultivar_name=cultivar_name)
        return cultivar.first()
    except Cultivar.DoesNotExist:
        return None

def get_labtest_from_db(sku):
    """
    Return labtest from db.
    """
    try:
        labtest = LabTest.objects.filter(Inventory_SKU=sku)
        return labtest.first()
    except LabTest.DoesNotExist as exc:
        print(exc)
        return None

def check_documents(inventory_name, record):
    """
    Check if record has any documents.
    """
    try:
        response = list()
        if record.get('image_name'):
            record = get_inventory_item(inventory_name, record['item_id'])
        if record.get('documents') and len(record['documents']) > 0:
            folder_name = f"{record['name']}-{record['item_id']}"
            folder_id = create_folder(INVENTORY_BOX_ID, folder_name)
            for document in record['documents']:
                if document['attachment_order'] == 1:
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

def fetch_inventory(inventory_name, days=1):
    """
    Fetch latest inventory from Zoho Inventory.
    """
    cultivar = None
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S-0000')
    has_more = True
    page = 0
    inventory_obj = get_inventory_obj(inventory_name)
    while has_more:
        records = inventory_obj.get_inventory(params={'page': page, 'last_modified_time': date})
        has_more = records['page_context']['has_more_page']
        page = records['page_context']['page'] + 1
        for record in records['items']:
            try:
                cultivar = get_cultivar_from_db(record['cf_strain_name'])
                if cultivar:
                    record['cultivar'] = cultivar
                labtest = get_labtest_from_db(record['sku'])
                if labtest:
                    record['labtest'] = labtest
                documents = check_documents(inventory_name, record)
                if documents and len(documents) > 0:
                    record['documents'] = documents
                obj = InventoryModel.objects.update_or_create(
                    item_id=record['item_id'],
                    name=record['name'],
                    cultivar=cultivar,
                    labtest=labtest,
                    defaults=record)
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
    inventory = get_inventory_obj(inventory_name)
    record = json.loads(unquote(response))['item']
    record = inventory.parse_item(response=record, is_detail=True)
    try:
        cultivar = get_cultivar_from_db(record['cf_strain_name'])
        if cultivar:
            record['cultivar'] = cultivar
        labtest = get_labtest_from_db(record['sku'])
        if labtest:
            record['labtest'] = labtest
        documents = check_documents(inventory_name, record)
        if documents and len(documents) > 0:
                record['documents'] = documents
        obj, created = InventoryModel.objects.update_or_create(
            item_id=record['item_id'],
            name=record['name'],
            cultivar=cultivar,
            labtest=labtest,
            defaults=record)
        return obj.item_id
    except Exception as exc:
        print(exc)
        return {}