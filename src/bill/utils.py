from bill.models import (Estimate, LineItem)
from bill.bill_format import (BILLS_FORMAT, )
from brand.models import License, LicenseProfile

def parse_fields(module, response, many=False):
    """
    Parse fields for books.
    """
    format_dict = BILLS_FORMAT[module]
    if many:
        result = list()
        for res in response:
            result.append({k:res.get(v, None) for k,v in format_dict.items() if res.get(v) != None})
        return result
    return {k:response.get(v, None) for k,v in format_dict.items() if response.get(v) != None}

def get_notify_addresses(notification_methods):
    """
    Get all email address that needs to be notified.
    """
    return [
        k for k, v in notification_methods.items() if 'notify' in v
    ]

def save_estimate(request):
    """
    Save estimate in db.
    """
    estimate = request.data
    customer_name = request.data.get('customer_name')
    line_items = request.data.get('line_items')
    del estimate['line_items']
    estimate_obj, created = Estimate.objects.update_or_create(customer_name=customer_name, defaults=estimate)
    items = list()
    for item in line_items:
        item_obj, created = LineItem.objects.update_or_create(estimate=estimate_obj, item_id=item.get('item_id'), defaults=item)
    return estimate_obj

def delete_estimate(customer_name=None):
    """
    Delete estimate from db.
    """
    if customer_name:
        try:
            obj = Estimate.objects.get(customer_name=customer_name)
            LineItem.objects.filter(estimate=obj).delete()
            obj.delete()
            return True
        except (LineItem.DoesNotExist, Estimate.DoesNotExist):
            return False
    return False

def save_estimate_from_intransit(in_transit_data):
    """
    Save estimate in db.
    """
    estimate = in_transit_data
    customer_name = in_transit_data.get('customer_name')
    line_items = in_transit_data.get('line_items')
    del estimate['line_items']
    estimate_obj, created = Estimate.objects.update_or_create(customer_name=customer_name, defaults=estimate)
    items = list()
    for item in line_items:
        item_obj, created = LineItem.objects.update_or_create(estimate=estimate_obj, item_id=item.get('item_id'), defaults=item)
    return estimate_obj


def parse_intransit_to_pending(data):
    """
    parse data according to model format.
    """
    
    line_items = [{"sku": item.get('sku',''),
                   "item_id": item.get('item_id',''),
                   "item_order": item.get('item_order'),
                   "quantity": item.get('order'),
                   "item_total": item.get('total'),
                   "description": item.get('description',''),
                   "rate": item.get('purchase_rate'),
                   "name": item.get('name')} for item in data.get('order_data').get('cart_item',[])]
    total = sum(int(i['total']) for i in data.get('order_data').get('cart_item',[]) if i['sku'] not in ['CT1','CT2','MCSP','PT1'])
    tax_total = sum(int(i['total']) for i in data.get('order_data').get('cart_item',[]) if i['sku'] in ['CT1','CT2'])
    license_profile_obj = LicenseProfile.objects.get(id=data.get('profile_id'))
    shipping_address = None
    if data.get('order_data').get('shipTo'):
        shipping_address = data.get('order_data').get('shipTo').get('premises_address')
    else:
        shipping_address = license_profile_obj.license.premises_address
    customer_name =  license_profile_obj.license.legal_business_name
    estimate_number = data.get('order_data').get('estimate_number')
    estimate_id = data.get('order_data').get('estimate_id')
    
    return {
        'line_items': line_items,
        'total': total,
        'tax_total': tax_total,
        'shipping_address': shipping_address,
        'customer_name':  customer_name,
        'estimate_number': estimate_number,
        'estimate_id': estimate_id
    }
    

        

    
    
    
    
