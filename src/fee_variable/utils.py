import decimal
from decimal import Decimal
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from brand.models import (License, LicenseProfile,)
from .models import (
    CustomInventoryVariable,
    VendorInventoryCategoryAccounts,
    VendorInventoryDefaultAccounts,
    VendorInventoryCategoryAccounts,
)


custom_inventory_variable_program_map = {
    'Spot Market': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_BRONZE,
    },
    'IFP - Silver - Right of First Refusal': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_SILVER,
    },
    'IFP - Gold - Exclusivity': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_GOLD,
    },
    'Silver - Member': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IBP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_SILVER,
    },
    'Gold - VIP': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IBP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_GOLD,
    },
    'IFP No Tier': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_NO_TIER,
    },
    'IBP No Tier': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IBP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_NO_TIER,
    },
}

# ITEM_CATEGORY_MSCP_FEE_VAR_MAP = {
#     'Flowers':       mcsp_fee',
#     'Trims':         mcsp_fee',
#     'Isolates':     'mcsp_fee_per_g',
#     'Concentrates': 'mcsp_fee_per_g',
#     'Terpenes':     'mcsp_fee_per_g',
#     'Clones':       'mcsp_fee_per_pcs',

ITEM_CATEGORY_MSCP_FEE_VAR_MAP = {
    'Flower - Tops':                'mcsp_fee_flower_tops',
    'Flower - Small':               'mcsp_fee_flower_smalls',
    'Trim':                         'mcsp_fee_trims',
    'Kief':                         'mcsp_fee_flower_tops',
    'Isolates':                     'mcsp_fee_isolates',
    'Isolates - CBD':               'mcsp_fee_isolates',
    'Isolates - THC':               'mcsp_fee_isolates',
    'Isolates - CBG':               'mcsp_fee_isolates',
    'Isolates - CBN':               'mcsp_fee_isolates',
    'Crude Oil':                    'mcsp_fee_concentrates',
    'Crude Oil - THC':              'mcsp_fee_concentrates',
    'Crude Oil - CBD':              'mcsp_fee_concentrates',
    'Distillate Oil':               'mcsp_fee_concentrates',
    'Distillate Oil - THC':         'mcsp_fee_concentrates',
    'Distillate Oil - CBD':         'mcsp_fee_concentrates',
    'Hash':                         'mcsp_fee_concentrates',
    'Shatter':                      'mcsp_fee_concentrates',
    'Sauce':                        'mcsp_fee_concentrates',
    'Crumble':                      'mcsp_fee_concentrates',
    'Badder':                       'mcsp_fee_concentrates',
    'Live Resin':                   'mcsp_fee_concentrates',
    'Rosin':                        'mcsp_fee_concentrates',
    'HTE':                          'mcsp_fee_concentrates',
    'HTE Diamonds':                 'mcsp_fee_concentrates',
    'Terpenes':                     'mcsp_fee_terpenes',
    'Terpenes - Cultivar Specific': 'mcsp_fee_terpenes',
    'Terpenes - Cultivar Blended':  'mcsp_fee_terpenes',
    'Clones':                       'mcsp_fee_clones',
}

ITEM_CATEGORY_MSCP_FEE_CONVERSION_MAP = {
    'Kief': lambda val: Decimal(val)/Decimal(453.59237), # convert lb to gram
}

PERCENTAGE_BASED_MSCP_FEE_ITEM_CATEGORIES = (
    'Isolates - CBD',
    'Isolates - THC',
    'Isolates - CBG',
    'Isolates - CBN',
    'Crude Oil',
    'Crude Oil - THC',
    'Crude Oil - CBD',
    'Distillate Oil',
    'Distillate Oil - THC',
    'Distillate Oil - CBD',
    'Hash',
    'Shatter',
    'Sauce',
    'Crumble',
    'Badder',
    'Live Resin',
    'Rosin',
    'HTE',
    'HTE Diamonds',
    'Terpenes - Cultivar Specific',
    'Terpenes - Cultivar Blended',
)


def get_item_mcsp_fee(vendor_name, license_profile=None, item_category=None, farm_price=None, request=None, no_tier_fee=True ):
    msg_error = lambda msg: messages.error(request, msg,) if request else None
    if item_category and item_category in ITEM_CATEGORY_MSCP_FEE_VAR_MAP:
        fee_var = ITEM_CATEGORY_MSCP_FEE_VAR_MAP[item_category]
        if not license_profile:
            lp = LicenseProfile.objects.filter(name=vendor_name).first()
        else:
            lp = license_profile
        if lp:
            if lp.license.status == 'approved':
                program_name = lp.signed_program_name or ''
                program_name = program_name.strip()
                if not program_name and no_tier_fee:
                    if lp.license.profile_category in ('microbusiness', 'manufacturing', 'retail', 'distribution', 'processing'):
                        program_name = 'IBP No Tier'
                    else:
                        program_name = 'IFP No Tier'
                    if request:
                        messages.warning(request, f'No signed program tier found for profile, using {program_name} MCSP fee.',)

                tier = custom_inventory_variable_program_map.get(program_name, {})
                inventory_variable = CustomInventoryVariable.objects.filter(**tier).order_by('-created_on').first()
                if inventory_variable and hasattr(inventory_variable, fee_var) and getattr(inventory_variable, fee_var) is not None:
                    try:
                        db_val = Decimal(getattr(inventory_variable, fee_var))
                    except decimal.InvalidOperation:
                        msg_error('Error while parsing MCSP fee from db.')
                        return None
                    else:
                        if item_category in ITEM_CATEGORY_MSCP_FEE_CONVERSION_MAP:
                            db_val = ITEM_CATEGORY_MSCP_FEE_CONVERSION_MAP[item_category](db_val)
                        if item_category in PERCENTAGE_BASED_MSCP_FEE_ITEM_CATEGORIES:
                            if farm_price is not None:
                                try:
                                    fp = Decimal(farm_price)
                                except decimal.InvalidOperation:
                                    msg_error('Error while parsing farm price for MCSP fee calculation.')
                                    return None
                                else:
                                    mcsp_fee = (fp*db_val)/Decimal('100')
                                    return mcsp_fee.quantize(Decimal('1.000000'), rounding=decimal.ROUND_DOWN)
                            else:
                                msg_error('Farm price not provided for MCSP fee calculation.')
                                return None
                        else:
                            return db_val.quantize(Decimal('1.000000'), rounding=decimal.ROUND_DOWN)
                else:
                    program_type_choices_dict = dict(CustomInventoryVariable.PROGRAM_TYPE_CHOICES)
                    program_tier_choices_dict = dict(CustomInventoryVariable.PROGRAM_TIER_CHOICES)
                    msg_error(
                        f"MCSP fee not found in Vendor Inventory Variables (fee var: '{fee_var}') for "
                        f"Program Type: '{program_type_choices_dict.get(tier.get('program_type'))}', "
                        f" Program Tier: '{program_tier_choices_dict.get(tier.get('tier'))}'."
                    )
            else:
                msg_error('Profile is not approved.')
        else:
            msg_error('License Profile not found.')
    else:
        if item_category:
                msg_error(f'MCSP fee is not mapped for Item category type \'{item_category}\'.')
        else:
            msg_error('Item category not supported or not defined.')

def get_new_items_accounts(zoho_organization: str, item_category: str):
    """
        get ids of sales account, purchase account and inventory account from database for new item.

    Args:
        zoho_organization (str): Zoho inventory organization.
                        choices: 'efd', 'efl', 'efn'.
        iteam_category (str): Vendor inventory iteam category.
                        eg. 'Flower - Tops', 'Flower - Small', 'Trim', 'Isolates - CBD',.
    Returns:
        dict: Dictionary of account ids for new vendor inventory item.
              sample:
              {
                  'account_id':           '2158711000001027029',
                  'purchase_account_id':  '2158711000001027033',
                  'inventory_account_id': '2158711000000198057',
              }
    """
    resp_dict = {}
    try:
        obj = VendorInventoryDefaultAccounts.objects.get(zoho_organization=zoho_organization)
    except VendorInventoryDefaultAccounts.DoesNotExist:
        pass
    else:
        try:
            cat_obj = obj.category_accounts_set.get(item_category=item_category)
        except VendorInventoryCategoryAccounts.DoesNotExist:
            resp_dict = obj.get_new_item_accounts_dict()
        else:
            resp_dict = cat_obj.get_new_item_accounts_dict()
    return resp_dict