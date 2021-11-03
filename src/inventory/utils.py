import decimal
from decimal import Decimal
from django.contrib import messages

from fee_variable.models import (TaxVariable, )
from .models import InTransitOrder
from .data import (CG, )


BIOMASS_TYPE_TO_TAX = {
    'Dried Flower': 'dried_flower_tax',
    'Dried Leaf':   'dried_leaf_tax',
    'Fresh Plant':  'fresh_plant_tax',
}

def get_tax_from_db(tax='dried_flower_tax', request=None):
    msg_error = lambda msg: messages.error(request, msg,) if request else None
    try:
        tax_var = TaxVariable.objects.latest('-created_on')
    except TaxVariable.DoesNotExist:
        msg_error('Tax variables not found in db.')
        return None
    else:
        try:
            return Decimal(getattr(tax_var, tax))
        except ValueError:
            msg_error('Error while fetching tax from db.')
            return None


def get_item_tax(category_name, biomass_type=None, biomass_input_g=None, total_batch_output=None, request=None):
    msg_error = lambda msg: messages.error(request, msg,) if request else print(msg)
    fixed_to_6 = lambda val: val.quantize(Decimal('1.000000'), rounding=decimal.ROUND_DOWN)
    if category_name:
        if CG.get(category_name, '') == 'Flowers':
            tax = get_tax_from_db(tax='dried_flower_tax')
            if isinstance(tax, Decimal):
                return tax
        elif CG.get(category_name, '') == 'Trims':
            tax = get_tax_from_db(tax='dried_leaf_tax')
            if isinstance(tax, Decimal):
                return tax
        elif CG.get(category_name, '') == 'Kief':
            tax = get_tax_from_db(tax='dried_leaf_tax')
            if isinstance(tax, Decimal):
                fixed_to_6(tax/Decimal('453.59237'))
        elif CG.get(category_name, '') in ('Isolates', 'Distillates', 'Concentrates'):

            if biomass_type:
                biomass_tax_lb = get_tax_from_db(tax=BIOMASS_TYPE_TO_TAX.get(biomass_type))
                if isinstance(biomass_tax_lb, Decimal):
                    biomass_tax_g = biomass_tax_lb/Decimal('453.59237')
                    if biomass_input_g:
                        if total_batch_output:
                            return fixed_to_6(biomass_tax_g * Decimal(biomass_input_g)) / Decimal(total_batch_output)
                        else:
                            msg_error('Item does not have a Batch output quantity to calculate the tax.')
                            return None
                    else:
                        msg_error('Item do not have a quantity of Biomass used to produce the item.')
                        return None
            else:
                msg_error('Biomass type is not provided to calculate the tax.')
                return None
        elif CG.get(category_name, '') in ('Clones', 'Terpenes'):
            return Decimal(0.0)
        else:
            msg_error('No Cultivar Tax is defined for selected category.')
            return None

    msg_error('No Cultivar Tax found.')
    return None


def delete_in_transit_item(estimate_id):
    """
    Remove item from InTransitOrder
    """
    transit_orders = InTransitOrder.objects.filter(order_data__estimate_id=estimate_id)
    if transit_orders:
        transit_orders.delete()
        

        
