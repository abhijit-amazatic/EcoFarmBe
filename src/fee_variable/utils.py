from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from brand.models import (License, LicenseProfile,)
from .models import (CustomInventoryVariable, TaxVariable, VendorInventoryDefaultAccounts)


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
    'Flowers':      'mcsp_fee_flowers',
    'Trims':        'mcsp_fee_trims',
    'Concentrates': 'mcsp_fee_concentrates',
    'Isolates':     'mcsp_fee_isolates',
    'Terpenes':     'mcsp_fee_terpenes',
    'Clones':       'mcsp_fee_clones',
}
ITEM_CATEGORY_MSCP_FEE_IN_PERCENTAGE = ('Isolates', 'Concentrates', 'Terpenes')


def get_item_mcsp_fee(vendor_name, license_profile=None, item_category_group=None, farm_price=None, request=None, no_tier_fee=True ):
    msg_error = lambda msg: messages.error(request, msg,) if request else None
    if item_category_group and item_category_group in ITEM_CATEGORY_MSCP_FEE_VAR_MAP :
        fee_var = ITEM_CATEGORY_MSCP_FEE_VAR_MAP[item_category_group]
        if not license_profile:
            lp = LicenseProfile.objects.filter(name=vendor_name).first()
        else:
            lp = license_profile
        if lp:
            if lp.license.status == 'approved':
                program_name = None
                try:
                    program_overview = lp.license.program_overview
                    program_name = program_overview.program_details.get('program_name')
                except ObjectDoesNotExist:
                    pass
                    # self.message_user(request, 'program overview not exist', level='error')
                if not program_name and no_tier_fee:
                    if lp.license.is_buyer:
                        program_name = 'IBP No Tier'
                    else:
                        program_name = 'IFP No Tier'
                    if request:
                        messages.warning(request, f'No program tier found for profile, using {program_name} MCSP fee.',)

                tier = custom_inventory_variable_program_map.get(program_name, {})
                InventoryVariable = CustomInventoryVariable.objects.filter(**tier).order_by('-created_on').first()
                if InventoryVariable and hasattr(InventoryVariable, fee_var) and getattr(InventoryVariable, fee_var) is not None:
                    try:
                        db_val = float(getattr(InventoryVariable, fee_var))
                    except ValueError:
                        msg_error('Error while parsing MCSP fee from db.')
                        return None
                    else:
                        if item_category_group in ITEM_CATEGORY_MSCP_FEE_IN_PERCENTAGE:
                            if farm_price is not None:
                                try:
                                    fp = float(farm_price)
                                except ValueError:
                                    msg_error('Error while parsingfarm price for MCSP fee calculation.')
                                    return None
                                else:
                                    return round((fp*db_val)/100, 2)
                            else:
                                msg_error('Farm price not provided for MCSP fee calculation.')
                                return None
                        else:
                            return db_val
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
        msg_error('Item category not defined or not valid.')

def get_new_items_accounts(zoho_organization: str):
    """
        get ids of sales account, purchase account and inventory account from database for new item.

    Args:
        zoho_org (str): Zoho inventory organization.
                        choices: 'efd', 'efl', 'efn'.

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
        resp_dict = obj.get_new_item_accounts_dict()
    return resp_dict