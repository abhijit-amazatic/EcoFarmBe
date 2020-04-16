from core.settings import (
    INVENTORY_CLIENT_ID,
    INVENTORY_CLIENT_SECRET,
    INVENTORY_REFRESH_TOKEN,
    INVENTORY_REDIRECT_URI,
    INVENTORY_ORGANIZATION_ID,
)
from pyzoho.inventory import Inventory

def get_inventory_items(params={}):
    """
    Return Inventory list.
    """
    inventory = Inventory(
        client_id=INVENTORY_CLIENT_ID,
        client_secret=INVENTORY_CLIENT_SECRET,
        refresh_token=INVENTORY_REFRESH_TOKEN,
        redirect_uri=INVENTORY_REDIRECT_URI,
        organization_id=INVENTORY_ORGANIZATION_ID
    )
    return inventory.get_inventory(params=params)

def get_inventory_item(item_id):
    """
    Return inventory item.
    """
    inventory = Inventory(
        client_id=INVENTORY_CLIENT_ID,
        client_secret=INVENTORY_CLIENT_SECRET,
        refresh_token=INVENTORY_REFRESH_TOKEN,
        redirect_uri=INVENTORY_REDIRECT_URI,
        organization_id=INVENTORY_ORGANIZATION_ID
    )
    return inventory.get_inventory(item_id=item_id)