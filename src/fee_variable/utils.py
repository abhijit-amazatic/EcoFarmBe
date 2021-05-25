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



def get_mcsp_fee(vendor_name, request=None, no_tier_fee=True ):
    lp = LicenseProfile.objects.filter(name=vendor_name).first()
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
            if InventoryVariable and hasattr(InventoryVariable, 'mcsp_fee'):
                return float(InventoryVariable.mcsp_fee)
            else:
                program_type_choices_dict = dict(CustomInventoryVariable.PROGRAM_TYPE_CHOICES)
                program_tier_choices_dict = dict(CustomInventoryVariable.PROGRAM_TIER_CHOICES)
                if request:
                    messages.error(
                        request,
                        (
                            'MCSP fee not found in Vendor Inventory Variables for '
                            f"Program Type: '{program_type_choices_dict.get(tier.get('program_type'))}' "
                            f"and Program Tier: '{program_tier_choices_dict.get(tier.get('tier'))}'."
                        ),
                    )
        else:
            if request:
                messages.error(request, 'Profile is not approved.')
    else:
        if request:
            messages.error(request, 'License Profile not found.')

