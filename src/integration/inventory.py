from datetime import (datetime, timedelta)
from core.settings import (
    INVENTORY_CLIENT_ID,
    INVENTORY_CLIENT_SECRET,
    INVENTORY_REFRESH_TOKEN,
    INVENTORY_REDIRECT_URI,
    INVENTORY_ORGANIZATION_ID,
)
from pyzoho.inventory import Inventory
from .models import (Integration, )
from inventory.models import Inventory as InventoryModel

def get_inventory_items(params={}):
    """
    Return Inventory list.
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
    return inventory.get_inventory(params=params)

def get_inventory_item(item_id):
    """
    Return inventory item.
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
    return inventory.get_inventory(item_id=item_id)

def fetch_inventory(days=1):
    """
    Fetch latest inventory from Zoho Inventory.
    """
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S-0000')
    records = get_inventory_items({'last_modified_time': date})
    for record in records['items']:
        try:
            obj = InventoryModel.objects.update_or_create(item_id=record['item_id'], name=record['name'], defaults=record)
        except Exception as exc:
            print(exc)
            continue