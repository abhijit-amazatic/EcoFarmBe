import re
from datetime import date
from decimal import Decimal
from django.utils import timezone
from django.contrib import messages

from core.celery import (app,)
from integration.inventory import (
    get_inventory_obj,
    update_inventory_item
)
from fee_variable.utils import (
    get_item_mcsp_fee,
)

from brand.models import (LicenseProfile,)
from ..data import (
    ITEM_CUSTOM_FIELD_ORG_MAP,
)
from ..utils import (
    get_item_tax
)
from ..models import (
    Inventory,
)


@app.task(queue="general")
def update_zoho_item_tax(item_ids=[], org='efd'):
    orgs = ('efd', 'efl', 'efn')
    qs = Inventory.objects.filter(item_type='inventory')
    if item_ids:
        qs = qs.filter(pk__in=item_ids)
    else:
        qs = Inventory.objects.filter(
            cf_cfi_published=True,
            status='active',
            cf_farm_price_2__isnull=False,
        )

    if org in orgs:
        qs = qs.filter(inventory_name=org.upper())
    elif org == 'all':
        qs = qs.filter(inventory_name__in=[x.upper() for x in orgs])
    else:
        qs = qs.none()

    print(f'Item count: {qs.count()}')
    
    for item in qs.all():
        print(f'\nUpdating Tax for item {item.pk}: {item.name}')
        lp=None
        lp_qs = LicenseProfile.objects.filter(
            **{f'license__zoho_books_vendor_ids__{item.inventory_name.lower()}': item.vendor_id}
        )
        if lp_qs.exists():
            lp = lp_qs.first()
        mcsp_fee = get_item_mcsp_fee(
            item.cf_vendor_name,
            item_category=item.category_name,
            farm_price=item.cf_farm_price_2,
        )
        if isinstance(mcsp_fee, Decimal):
            cultivation_tax = get_item_tax(
                category_name=item.category_name,
                biomass_type=item.cf_biomass,
                biomass_input_g=item.cf_raw_material_input_g,
                total_batch_output=item.cf_batch_qty_g,
                # request=request,
            )
            if isinstance(cultivation_tax, Decimal):
                data = {
                    'cf_mscp': mcsp_fee,
                    'cf_cultivation_tax': cultivation_tax,
                }
                if item.cf_farm_price_2:
                    price = Decimal(item.cf_farm_price_2) + mcsp_fee + cultivation_tax
                    if isinstance(price, Decimal):
                        price = f"{price.normalize():f}"
                    data['price'] = price
                    data['rate'] = price
                inventory_org = (item.inventory_name or '').lower()
                if inventory_org in ('efd', 'efn', 'efl'):
                    inventory_name = f'inventory_{inventory_org}'

                    data_type_conversion_map = {
                        float: lambda v: str(v),
                        date: lambda v: v.strftime("%Y-%m-%d"),
                        Decimal: lambda v: f"{v.normalize():f}",
                    }
                    if data and inventory_org in ITEM_CUSTOM_FIELD_ORG_MAP:
                        final_data = dict()
                        org_cf_map = ITEM_CUSTOM_FIELD_ORG_MAP[inventory_org]
                        for k, v in data.items():
                            if type(v) in data_type_conversion_map:
                                v = data_type_conversion_map[type(v)](v)
                            if k.startswith('cf_'):
                                if k in org_cf_map:
                                    final_data[org_cf_map[k]] = v
                            else:
                                final_data[k] = v
                        data = final_data

                    try:
                        result = update_inventory_item(inventory_name, item.item_id, data)
                    except Exception as exc:
                        print('  Exception while updating item in Zoho Inventory')
                        print(f'  {exc}')
                        print('Data: ', data)
                    else:
                        if result.get('code') == 0:
                            print(f"  Farm price: {item.cf_farm_price_2}")
                            print(f"  MCSP Fee: {item.cf_mscp} -> {data['cf_mscp']}")
                            print(f"  Cultivation Tax: {item.cf_cultivation_tax} -> {data['cf_cultivation_tax']}")
                            print(f"  Price: {item.price} -> {data['price']}")
                        else:
                            print('  Error while updating item in Zoho Inventory')
                            print('  response: ', result)
                            print('  Data: ', data)
            else:
                print('  Unable to calculate Cultivation Tax.')
        else:
            print('  Unable to calculate MCSP Fee.')
