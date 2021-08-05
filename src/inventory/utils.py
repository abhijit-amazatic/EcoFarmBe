from django.contrib import messages

from fee_variable.models import (TaxVariable, )
from .models import InTransitOrder
from .data import (CG, )


def get_tax_from_db(tax='flower', request=None):
    msg_error = lambda msg: messages.error(request, msg,) if request else None
    try:
        tax_var = TaxVariable.objects.latest('-created_on')
    except TaxVariable.DoesNotExist:
        pass
    else:
        if tax == 'flower':
            tax = 'cultivar_tax'
        elif tax == 'trim':
            tax = 'trim_tax'
        else:
            tax = None
        if tax:
            try:
                return float(getattr(tax_var, tax))
            except ValueError:
                msg_error('Error while parsing tax from db.')
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
        if CG.get(category_name, '') in ('Isolates', 'Concentrates'):
            trim_tax = get_tax_from_db(tax='trim')
            if isinstance(trim_tax, float):
                if trim_used:
                    if item_quantity:
                        tax = (trim_tax * trim_used) / item_quantity
                        return round(tax, 2)
                    else:
                        msg_error('Item does not have a Batch quantity to calculate.')
                        return None
                else:
                    msg_error('Item does not have a quantity of Trim used to produce the item.')
                    return None
        if CG.get(category_name, '') in ('Clones', 'Terpenes'):
            return float(0.0)
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
        
