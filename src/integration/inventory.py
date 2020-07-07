import json
from datetime import (datetime, timedelta)
from urllib.parse import (unquote, )
from core.settings import (
    INVENTORY_CLIENT_ID,
    INVENTORY_CLIENT_SECRET,
    INVENTORY_REFRESH_TOKEN,
    INVENTORY_REDIRECT_URI,
    INVENTORY_ORGANIZATION_ID,
)
from pyzoho.inventory import Inventory
from .models import (Integration, )
from labtest.models import (LabTest, )
from inventory.models import Inventory as InventoryModel
from cultivar.models import (Cultivar, )
from integration.crm import (get_labtest, )

def get_inventory_obj():
    """
    Return pyzoho.inventory object.
    """
    try:
        token = Integration.objects.get(name='inventory')
        access_token = token.access_token
        access_expiry = token.access_expiry
    except Integration.DoesNotExist:
        access_token = access_expiry = None
    inventory = Inventory(
        client_id=INVENTORY_CLIENT_ID,
        client_secret=INVENTORY_CLIENT_SECRET,
        refresh_token=INVENTORY_REFRESH_TOKEN,
        redirect_uri=INVENTORY_REDIRECT_URI,
        organization_id=INVENTORY_ORGANIZATION_ID,
        access_token=access_token,
        access_expiry=access_expiry
    )
    if not access_token and not access_expiry:
        Integration.objects.update_or_create(
            name='inventory',
            client_id=inventory.CLIENT_ID,
            client_secret=inventory.CLIENT_SECRET,
            access_token=inventory.ACCESS_TOKEN,
            access_expiry=inventory.ACCESS_EXPIRY[0],
            refresh_token=inventory.REFRESH_TOKEN
        )
    return inventory

def get_inventory_items(params={}):
    """
    Return Inventory list.
    """
    inventory = get_inventory_obj()
    return inventory.get_inventory(params=params)

def get_inventory_item(item_id):
    """
    Return inventory item.
    """
    inventory = get_inventory_obj()
    return inventory.get_inventory(item_id=item_id)

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

def fetch_inventory(days=1):
    """
    Fetch latest inventory from Zoho Inventory.
    """
    cultivar = None
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S-0000')
    has_more = True
    page = 0
    while has_more:
        records = get_inventory_items({'page': page, 'last_modified_time': date})
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
                obj = InventoryModel.objects.update_or_create(
                    item_id=record['item_id'],
                    name=record['name'],
                    cultivar=cultivar,
                    labtest=labtest,
                    defaults=record)
            except Exception as exc:
                print(exc)
                continue
        
def sync_inventory(response):
    """
    Webhook for Zoho inventory to sync inventory real time.
    """
    inventory = get_inventory_obj()
    record = json.loads(unquote(response))['item']
    record = inventory.parse_item(response=record, is_detail=True)
    try:
        cultivar = get_cultivar_from_db(record['cf_strain_name'])
        if cultivar.count() > 0:
            record['cultivar'] = cultivar.first()
        obj, created = InventoryModel.objects.update_or_create(
            item_id=record['item_id'],
            name=record['name'],
            cultivar=cultivar.first(),
            defaults=record)
        return obj.item_id
    except Exception as exc:
        print(exc)
        return {}