from django.contrib import messages

from brand.models import (License, LicenseProfile,)
from .models import (CustomInventoryVariable, TaxVariable)


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

ITEM_CATEGORY_MSCP_FEE_VAR_MAP = {
    'Flowers':       'mcsp_fee',
    'Trims':         'mcsp_fee',
    'Isolates':     'mcsp_fee_per_g',
    'Concentrates': 'mcsp_fee_per_g',
    'Terpenes':     'mcsp_fee_per_g',
    'Clones':       'mcsp_fee_per_pcs',
}


def get_item_mcsp_fee(vendor_name, license_profile=None, item_category_group=None, request=None, no_tier_fee=True ):

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
                except License.program_overview.RelatedObjectDoesNotExist:
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
                if InventoryVariable and hasattr(InventoryVariable, fee_var):
                    return float(getattr(InventoryVariable, fee_var))
                else:
                    program_type_choices_dict = dict(CustomInventoryVariable.PROGRAM_TYPE_CHOICES)
                    program_tier_choices_dict = dict(CustomInventoryVariable.PROGRAM_TIER_CHOICES)
                    if request:
                        messages.error(
                            request,
                            (
                                f"MCSP fee not found in Vendor Inventory Variables (fee var: '{fee_var}') for "
                                f"Program Type: '{program_type_choices_dict.get(tier.get('program_type'))}', "
                                f" Program Tier: '{program_tier_choices_dict.get(tier.get('tier'))}'."
                            ),
                        )
            else:
                if request:
                    messages.error(request, 'Profile is not approved.')
        else:
            if request:
                messages.error(request, 'License Profile not found.')
    else:
        if request:
            messages.error(request, 'Item category not defined or not valid.')

