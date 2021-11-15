from os import urandom
from decimal import Decimal
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe

from core import settings
from  fee_variable.utils import (get_new_items_accounts,)

from integration.inventory import (
    get_user_id,
)

from ..data import (
    # CUSTOM_INVENTORY_ITEM_DEFAULT_ACCOUNTS,
    ITEM_CUSTOM_FIELD_ORG_MAP,
)

def get_new_item_data(obj, inv_obj, item_name, category_id, vendor_id,):
    data = {}
    # data.update(CUSTOM_INVENTORY_ITEM_DEFAULT_ACCOUNTS.get(inv_obj.ORGANIZATION_ID, {}))
    data.update(
        get_new_items_accounts(
            zoho_organization=obj.zoho_organization,
            item_category=obj.category_name,
        )
    )
    data['category_name'] = obj.category_name
    data['category_id'] = category_id
    data['name'] = item_name
    data['item_type'] = 'inventory'
    data['unit'] = obj.unit
    data['is_taxable'] = True
    data['product_type'] = 'goods'
    data['cf_vendor_name'] = vendor_id
    data['cf_client_code'] = obj.client_code
    data['cf_client_id'] = obj.license_profile.license.client_id

    data['cf_strain_name'] = obj.get_cultivar_name
    data['cf_cultivar_type'] = obj.get_cultivar_type

    if obj.product_quality_notes:
        data['cf_batch_quality_notes'] = obj.product_quality_notes

    if obj.pricing_position:
        data['cf_seller_position'] = obj.pricing_position

    if obj.payment_terms:
        data['cf_payment_terms'] = obj.payment_terms

    if obj.payment_method:
        data['cf_payment_method'] = obj.payment_method

    if obj.cultivation_type:
        data['cf_cultivation_type'] = obj.cultivation_type

    if obj.procurement_rep:
        pro_rep_id = get_user_id(inv_obj, obj.procurement_rep)
        if pro_rep_id:
            data['cf_procurement_rep'] = pro_rep_id

    data['cf_status'] = obj.marketplace_status

    data['cf_farm_price_2'] = obj.farm_ask_price
    # data['purchase_rate'] = obj.farm_ask_price
    data['cf_cultivation_tax'] = obj.cultivation_tax
    data['cf_mscp'] = obj.mcsp_fee
    data['rate'] = obj.farm_ask_price + obj.cultivation_tax + obj.mcsp_fee


    if obj.need_lab_testing_service is not None:
        data['cf_lab_testing_services'] = 'Yes' if obj.need_lab_testing_service else 'No'


    data['cf_sample_in_house'] = 'Pending'

    # if obj.have_minimum_order_quantity:
    #     data['cf_minimum_quantity'] = int(obj.minimum_order_quantity)

    # if not settings.PRODUCTION and obj.zoho_organization in ('efl', 'efn'):
    #     data['cf_cfi_published'] = False
    # else:
    #     data['cf_cfi_published'] = True
    data['cf_cfi_published'] = True


    if obj.category_group in ('Flowers', 'Trims'):

        data['cf_date_available'] = str(obj.batch_availability_date or '')
        data['cf_harvest_date'] = str(obj.harvest_date or '')
        data['cf_flower_smalls'] = obj.category_name in ('Flower - Small',)
        if obj.category_group == 'Flowers':
            if obj.marketplace_status not in ('Vegging', 'Flowering'):
                data['cf_grade_seller'] = obj.grade_estimate
        if obj.marketplace_status in ('Vegging', 'Flowering', 'Processing'):
            if obj.quantity_available:
                data['cf_quantity_estimate'] = int(obj.quantity_available)

    elif obj.category_group in ('Kief', 'Terpenes',):

        data['cf_date_available'] = str(obj.batch_availability_date or '')
        if obj.manufacturing_date:
            data['cf_manufacturing_date'] = str(obj.manufacturing_date)

    elif obj.category_group in ('Concentrates', 'Isolates', 'Distillates'):

        data['cf_date_available'] = str(obj.batch_availability_date or '')
        data['cf_biomass'] = obj.biomass_type
        data['cf_raw_material_input_g'] = obj.biomass_input_g
        data['cf_batch_qty_g'] = obj.total_batch_quantity
        if obj.manufacturing_date:
            data['cf_manufacturing_date'] = str(obj.manufacturing_date)

        if obj.cannabinoid_type:
            data['cf_cannabinoid_type'] = obj.cannabinoid_type

        if obj.cannabinoid_percentage:
            data['cf_cannabinoid_percentage'] = obj.cannabinoid_percentage

    elif obj.category_group in ('Clones'):

        data['cf_rooting_time'] = obj.rooting_days

        # if obj.marketplace_status == 'Available' and obj.batch_availability_date:
        #     data['cf_date_available'] = str(obj.batch_availability_date)

        if obj.marketplace_status in ('Rooting',):
            if obj.quantity_available:
                data['cf_quantity_estimate'] = int(obj.quantity_available)

        # if obj.clone_date:
        #     data['cf_clone_date'] = str(obj.clone_date)

        if obj.clone_size:
            data['cf_clone_size_in'] = obj.clone_size
    else:
        data = {}

    if data and obj.zoho_organization in ITEM_CUSTOM_FIELD_ORG_MAP:
        final_data = dict()
        org_cf_map = ITEM_CUSTOM_FIELD_ORG_MAP[obj.zoho_organization]
        for k, v in data.items():
            if isinstance(v, Decimal):
                v = f"{v.normalize():f}"
            if k.startswith('cf_'):
                if k in org_cf_map:
                    final_data[org_cf_map[k]] = v
            else:
                final_data[k] = v
        return final_data
    return {}


