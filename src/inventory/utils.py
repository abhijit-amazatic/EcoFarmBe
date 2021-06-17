from django.contrib import messages

from fee_variable.models import (TaxVariable, )
from .data import (CG, )


def get_tax_from_db(tax='flower', request=None):
    try:
        tax_var = TaxVariable.objects.latest('-created_on')
    except TaxVariable.DoesNotExist:
        pass
    else:
        if tax=='flower':
            tax='cultivar_tax'
        elif tax=='trim':
            tax='trim_tax'
        else:
            tax = None
        if tax:
            try:
                return float(getattr(tax_var, tax))
            except ValueError:
                return None


def get_item_tax(category_name, trim_used=None, item_quantity=None, request=None):
    msg_error = lambda msg: messages.error(request, msg,) if request else None
    if category_name:
        if CG.get(category_name, '')  == 'Flowers':
            tax = get_tax_from_db(tax='flower')
            if isinstance(tax, float):
                return tax
        if CG.get(category_name, '') == 'Trims':
            tax = get_tax_from_db(tax='trim')
            if isinstance(tax, float):
                return tax
        if CG.get(category_name, '') in ('Isolates', 'Concentrates', 'Terpenes'):
            trim_tax = get_tax_from_db(tax='trim')
            if isinstance(trim_tax, float):
                if trim_used:
                    return (trim_tax * trim_used) / item_quantity
                else:
                    msg_error('Not provided quantity of Trim used to produce the item.')
                    return None
        if CG.get(category_name, '') == 'Clones':
            return float(0.0)
        else:
            msg_error('No Cultivar Tax is defined for selected category.')
            return None

    msg_error('No Cultivar Tax found.')
    return None