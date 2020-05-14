from datetime import (datetime, timedelta, )
from core.settings import (
    BOOKS_CLIENT_ID,
    BOOKS_CLIENT_SECRET,
    BOOKS_ORGANIZATION_ID,
    BOOKS_REDIRECT_URI,
    BOOKS_REFRESH_TOKEN,
    ESTIMATE_TAXES
)
from pyzoho.books import (Books, )
from .models import (Integration, )
from .inventory import (get_inventory_items, )


def get_books_obj():
    """
    Get Pyzoho books object.
    """
    try:
        token = Integration.objects.get(name='books')
        access_token = token.access_token
        access_expiry = token.access_expiry
    except Integration.DoesNotExist:
        access_token = access_expiry = None
    books_obj = Books(
        client_id=BOOKS_CLIENT_ID,
        client_secret=BOOKS_CLIENT_SECRET,
        redirect_uri=BOOKS_REDIRECT_URI,
        organization_id=BOOKS_ORGANIZATION_ID,
        refresh_token=BOOKS_REFRESH_TOKEN
    )
    if books_obj._refreshed:
        Integration.objects.update_or_create(
            name='books',
            client_id=BOOKS_CLIENT_ID,
            client_secret=BOOKS_CLIENT_SECRET,
            refresh_token=BOOKS_REFRESH_TOKEN,
            access_token=books_obj.access_token,
            access_expiry=books_obj.access_expiry
    )
    return books_obj
        
def create_contact(data, params=None):
    """
    Create contact in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.create_contact(data, parameters=params)

def get_item_dict(book, inventory):
    """
    Return Zoho Book item.
    """
    return {
        'item_id': book.get('item_id'),
        'sku': book.get('sku'),
        'name': book.get('name'),
        'rate': inventory.get('rate', book.get('rate')),
        'quantity': inventory.get('quantity'),
        'category_name': inventory.get('category_name')
    }

def get_tax(obj, tax):
    """
    Return tax information.
    """
    tax_obj = obj.Items()
    return tax_obj.list_items(parameters={'name': tax})

def get_item(obj, data):
    """
    Return item from Zoho books with applied tax.
    """
    taxes = ESTIMATE_TAXES
    line_items = list()
    for line_item in data.get('line_items'):
        item_obj = obj.Items()
        book_item = item_obj.list_items(parameters={'search_text': line_item['sku']})
        if len(book_item) == 1:
            book_item = book_item[0]
        elif len(book_item) > 1:
            for i in book_item:
                if i['sku'] == line_item['sku']:
                    book_item = i
                    break
        else:
            return {'code': 1003, 'message': 'Item not in zoho books.'}
        item = get_item_dict(book_item, line_item)
        line_items.append(item)
    flower_quantity = 0
    trim_quantity = 0
    for line_item in line_items:
        if line_item['category_name'] == 'Flower':
            flower_quantity += int(line_item['quantity'])
        elif line_item['category_name'] == 'Trim':
            trim_quantity += int(line_item['quantity'])
    if flower_quantity > 0:
        tax = get_tax(obj, taxes['Flower'])
        if len(tax) == 1:
            tax = tax[0]
        elif len(tax) > 1:
            for i in tax:
                if i['name'] == taxes['Flower']:
                    tax = i
                    break
        else:
            return {'code': 1003, 'message': 'Tax not in zoho books.'}
        line_items.append({
                'item_id': tax['item_id'],
                'rate': tax['rate'],
                'quantity': flower_quantity})
        line_items.append({
                'item_id': tax['item_id'],
                'rate': -int(tax['rate']),
                'quantity': flower_quantity})
    if trim_quantity > 0:
        tax = get_tax(obj, taxes['Trim'])
        if len(tax) == 1:
            tax = tax[0]
        elif len(tax) > 1:
            for i in tax:
                if i['name'] == taxes['Trim']:
                    tax = i
                    break
        else:
            return {'code': 1003, 'message': 'Tax not in zoho books.'}
        line_items.append({
                'item_id': tax['item_id'],
                'rate': tax['rate'],
                'quantity': trim_quantity})
        line_items.append({
                'item_id': tax['item_id'],
                'rate': -int(tax['rate']),
                'quantity': trim_quantity})
    data['line_items'] = line_items
    return {'code': 0, 'data': data}

def get_customer(obj, data):
    """
    Return customer from Zoho books using Zoho Inventory name.
    """
    contact_obj = obj.Contacts()
    customer = contact_obj.list_contacts(parameters={'contact_name': data['customer_name']})
    if len(customer) == 1:
        customer = customer[0]
    elif len(customer) > 1:
        for i in customer:
            if i['contact_name'] == data['customer_name']:
                customer = i
    else:
        return {'code': 1003, 'message': 'Contact not in zoho books.'}
    data['customer_id'] = customer['contact_id']
    return {'code': 0, 'data': data}

def create_estimate(data, params=None):
    """
    Create estimate in Zoho Books.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    result = get_customer(obj, data)
    print('result', result)
    if result['code'] != 0:
        return result
    result = get_item(obj, result['data'])
    print('result', result)
    if result['code'] != 0:
        return result
    return estimate_obj.create_estimate(result['data'], parameters=params)

def get_estimate(estimate_id, params=None):
    """
    Get an estimate.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.get_estimate(estimate_id, parameters=params)

def list_estimates(params=None):
    """
    List estimates.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.list_estimates(parameters=params)

def get_contact(contact_id, params=None):
    """
    Get contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.get_contact(contact_id, parameters=params)

def list_contacts(params=None):
    """
    List contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.list_contacts(parameters=params)