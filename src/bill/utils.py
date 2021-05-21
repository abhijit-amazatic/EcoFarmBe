from bill.models import (Estimate, LineItem)
from bill.bill_format import (BILLS_FORMAT, )

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