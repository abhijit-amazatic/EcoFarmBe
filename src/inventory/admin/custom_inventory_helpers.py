from os import urandom
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe

from core import settings

from integration.inventory import (
    get_user_id,
)

from ..data import (CUSTOM_INVENTORY_ITEM_DEFAULT_ACCOUNTS, CATEGORY_GROUP_MAP)

CG = {cat: k for k, v in CATEGORY_GROUP_MAP.items() for cat in v}

ITEM_CATEGORY_UNIT_MAP = {
    'Flowers':      'lb',
    'Trims':        'lb',
    'Isolates':     'g',
    'Concentrates': 'g',
    'Terpenes':     'g',
    'Clones':       'pcs',
}


def get_new_item_data(obj, inv_obj, category_id, vendor_id, tax, mcsp_fee):
    data = {}
    data.update(CUSTOM_INVENTORY_ITEM_DEFAULT_ACCOUNTS.get(inv_obj.ORGANIZATION_ID, {}))
    data['category_name'] = obj.category_name
    data['category_id'] = category_id
    data['name'] = obj.cultivar.cultivar_name
    data['item_type'] = 'inventory'
    data['unit'] = ITEM_CATEGORY_UNIT_MAP.get(CG.get(obj.category_name, ''), '')
    data['is_taxable'] = True
    data['product_type'] = 'goods'

    if obj.zoho_organization == 'efd':

        data['cf_vendor_name'] = vendor_id
        if obj.procurement_rep:
            pro_rep_id = get_user_id(inv_obj, obj.procurement_rep)
            if pro_rep_id:
                data['cf_procurement_rep'] = pro_rep_id
        data['cf_client_code'] = obj.client_code
        data['cf_cultivar_name'] = obj.cultivar.cultivar_name
        data['cf_strain_name'] = obj.cultivar.cultivar_name

        if obj.cultivar.cultivar_type:
            data['cf_cultivar_type'] = obj.cultivar.cultivar_type

        if obj.batch_availability_date:
            data['cf_date_available'] = str(obj.batch_availability_date)

        if obj.category_name in ('Flower - Small',):
            data['cf_flower_smalls'] = True

        if obj.marketplace_status in ('Vegging', 'Processing'):
            if obj.quantity_available:
                data['cf_quantity_estimate'] = int(obj.quantity_available)
        else:
            if obj.grade_estimate:
                data['cf_grade_seller'] = obj.grade_estimate

        if obj.harvest_date:
            data['cf_harvest_date'] = str(obj.harvest_date)

        if obj.product_quality_notes:
            data['cf_batch_quality_notes'] = obj.product_quality_notes

        if obj.need_lab_testing_service is not None:
            data['cf_lab_testing_services'] = 'Yes' if obj.need_lab_testing_service else 'No'

        if obj.farm_ask_price:
            data['cf_farm_price_2'] = obj.farm_ask_price
            # data['purchase_rate'] = obj.farm_ask_price
            data['rate'] = obj.farm_ask_price + tax + mcsp_fee

        if obj.pricing_position:
            data['cf_seller_position'] = obj.pricing_position
        if obj.have_minimum_order_quantity:
            data['cf_minimum_quantity'] = int(obj.minimum_order_quantity)

        if obj.payment_terms:
            data['cf_payment_terms'] = obj.payment_terms

        if obj.payment_method:
            data['cf_payment_method'] = obj.payment_method

        data['cf_status'] = obj.marketplace_status
        data['cf_sample_in_house'] = 'Pending'
        data['cf_cfi_published'] = True

    elif obj.zoho_organization == 'efl': #################  EFL

        data['cf_vendor_name'] = vendor_id
        data['cf_client_code'] = obj.client_code

        data['cf_cultivar_name'] = obj.cultivar.cultivar_name
        data['cf_strain_name'] = obj.cultivar.cultivar_name

        if obj.cultivar.cultivar_type:
            data['cf_cultivar_type'] = obj.cultivar.cultivar_type

        if obj.marketplace_status in ('Vegging', 'Flowering', 'Processing'):
            if obj.quantity_available:
                data['cf_quantity_estimate'] = int(obj.quantity_available)

        if obj.harvest_date:
            data['cf_manufacturing_date'] = str(obj.harvest_date)

        if obj.product_quality_notes:
            data['cf_batch_notes'] = obj.product_quality_notes

        if obj.farm_ask_price:
            data['cf_farm_price'] = obj.farm_ask_price
            # data['purchase_rate'] = obj.farm_ask_price
            data['rate'] = obj.farm_ask_price + tax + mcsp_fee

        data['cf_status'] = obj.marketplace_status
        # data['cf_sample_in_house'] = 'Pending'
        if settings.PRODUCTION:
            data['cf_cfi_published'] = True
        else:
            data['cf_cfi_published'] = False

    elif obj.zoho_organization == 'efn':  #################  EFN

        data['cf_vendor'] = vendor_id
        data['cf_client_code'] = obj.client_code

        data['cf_cultivar_name'] = obj.cultivar.cultivar_name

        if obj.cultivar.cultivar_type:
            data['cf_cultivar_type'] = obj.cultivar.cultivar_type

        if obj.marketplace_status in ('Rooting',):
            if obj.quantity_available:
                data['cf_quantity_estimate'] = int(obj.quantity_available)

        if obj.harvest_date:
            data['cf_clone_date'] = str(obj.harvest_date)

        if obj.product_quality_notes:
            data['cf_batch_quality_notes'] = obj.product_quality_notes

        if obj.farm_ask_price:
            data['cf_farm_price_pretax'] = obj.farm_ask_price
            # data['purchase_rate'] = obj.farm_ask_price
            data['rate'] = obj.farm_ask_price + tax + mcsp_fee

        if obj.payment_terms:
            data['cf_payment_terms'] = obj.payment_terms

        data['cf_status'] = obj.marketplace_status
        if settings.PRODUCTION:
            data['cf_publish_to_cfi'] = True
        else:
            data['cf_publish_to_cfi'] = False
    else:
        data = {}

    return data


