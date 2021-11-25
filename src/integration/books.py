import sys
import json
import base64
import redis
import traceback
from io import (BytesIO, )
from django.core.exceptions import (ObjectDoesNotExist,)
from datetime import (datetime, timedelta, )
from core import settings
from core.settings import (
    BOOKS_CLIENT_ID,
    BOOKS_CLIENT_SECRET,
    BOOKS_ORGANIZATION_EFD_ID,
    BOOKS_ORGANIZATION_EFL_ID,
    BOOKS_ORGANIZATION_EFN_ID,
    BOOKS_REDIRECT_URI,
    BOOKS_REFRESH_TOKEN,
    TRANSPORTATION_FEES,
    REDIS_URL,
    BOOKS_ORGANIZATION_LIST
)
from brand.models import (Brand, License, LicenseProfile, )
from pyzoho.books import (Books, )
from .models import (Integration, )
from .crm.crm_format import (CRM_FORMAT, )
from .books_format import (BOOKS_FORMAT_DICT, )
from .inventory import (get_inventory_items, update_inventory_item, get_inventory_name)
from .sign import (submit_estimate, )
from inventory.models import Inventory
from fee_variable.models import (TaxVariable, )

if not isinstance(BOOKS_ORGANIZATION_LIST, tuple):
    BOOKS_ORGANIZATION_LIST = BOOKS_ORGANIZATION_LIST.split(',')

def get_books_obj(books_name):
    """
    Get Pyzoho books object.
    """
    try:
        token = Integration.objects.get(name=books_name)
        access_token = token.access_token
        access_expiry = token.access_expiry
        refresh_token = token.refresh_token
    except Integration.DoesNotExist:
        access_token = access_expiry = None
        refresh_token = BOOKS_REFRESH_TOKEN
    if books_name == 'books_efd':
        BOOKS_ORGANIZATION_ID = BOOKS_ORGANIZATION_EFD_ID
    elif books_name == 'books_efl':
        BOOKS_ORGANIZATION_ID = BOOKS_ORGANIZATION_EFL_ID
    elif books_name == 'books_efn':
        BOOKS_ORGANIZATION_ID = BOOKS_ORGANIZATION_EFN_ID
    else:
        print(f'{books_name} organization not found.')
    books_obj = Books(
        client_id=BOOKS_CLIENT_ID,
        client_secret=BOOKS_CLIENT_SECRET,
        redirect_uri=BOOKS_REDIRECT_URI,
        organization_id=BOOKS_ORGANIZATION_ID,
        refresh_token=refresh_token,
        access_expiry=access_expiry,
        access_token=access_token)
    if books_obj.refreshed:
        Integration.objects.update_or_create(
            name=books_name,
            defaults={
                "name": books_name,
                "client_id":BOOKS_CLIENT_ID,
                "client_secret":BOOKS_CLIENT_SECRET,
                "refresh_token":books_obj.refresh_token,
                "access_token":books_obj.access_token,
                "access_expiry":books_obj.access_expiry[0]}
    )
    return books_obj

def get_format_dict(module):
    """
    Return Contact-CRM fields dictionary.
    """
    return CRM_FORMAT[module]


def update_available_for_sale(estimate):
    """
    Update inventory on basis of following contidions-
    - If estimate item is at ask price then decrease quantity from total item
      quantity available in marketplace (Not Zoho) and update Status in Zoho to "Pending Sale"
    - If estimate order item is converted to sales order  decrease item available quantity
      in marketplace (Not Zoho) and update Status in Zoho to "Pending Sale"
    """
    for item in estimate.get('line_items'):
        ask_price = item.get('ask_price')
        item_id = item.get('item_id')
        try:
            inventory = Inventory.objects.get(item_id=item_id)
        except Inventory.DoesNotExist:
            continue
        price = inventory.price
        if ask_price and price and (float(ask_price) >= float(price)):
            inventory.actual_available_stock -= int(item.get('quantity'))
            inventory.save()
            # inventory_name = get_inventory_name(item_id)
            # request = dict()
            # request['item_id'] = item_id
            # request['cf_status'] = 'Pending Sale'
            # response = update_inventory_item(inventory_name, item_id, request)
    return

def create_contact(books_name, data, params=None):
    """
    Create contact in Zoho Books.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.create_contact(data, parameters=params)

def update_contact(books_name, data, params=None):
    """
    Update contact in Zoho Books.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.update_contact(data.get('contact_id'), data, parameters=params)

def get_contact(books_name, contact_id, params=None):
    """
    Get contact.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.get_contact(contact_id, parameters=params)

def get_contact_addresses(books_name, contact_id):
    """
    Get contact address list.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.get_contact_addresses(contact_id)

def add_contact_address(books_name, contact_id, data, params=None):
    """
    Add contact address in Zoho Books.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.add_contact_address(contact_id, data, parameters=params)

def edit_contact_address(books_name, contact_id, address_id, data, params=None):
    """
    Edit contact address in Zoho Books.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.edit_contact_address(contact_id, address_id, data, parameters=params)

def get_contact_person(books_name, contact_id, contact_person_id, params=None):
    """
    Get contact person.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.ContactPersons()
    return contact_obj.get_contact_person(contact_id, contact_person_id, parameters=params)

def list_contact_persons(books_name, params=None):
    """
    List contact person.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.ContactPersons()
    return contact_obj.list_contact_persons(parameters=params)

def create_contact_person(books_name, data, params=None):
    """
    Create contact person.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.ContactPersons()
    return contact_obj.create_contact_person(data, parameters=params)

def update_contact_person(books_name, contact_person_id, data, params=None):
    """
    Update contact person.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.ContactPersons()
    return contact_obj.update_contact_person(contact_person_id, data, parameters=params)

def get_item_dict(book, inventory):
    """
    Return Zoho Book item.
    """
    data  = {
        'item_id': book.get('item_id'),
        'sku': book.get('sku'),
        'name': book.get('name'),
        'rate': inventory.get('rate', book.get('rate')),
        'quantity': inventory.get('quantity'),
        'category_name': inventory.get('category_name'),
        'item_custom_fields': inventory.get('item_custom_fields'),
        'ask_price': inventory.get('ask_price'),
        'description': inventory.get('description')
    }
    if inventory.get('warehouse_id'):
        data['warehouse_id'] = inventory.get('warehouse_id')
    return data

def get_tax(obj, tax):
    """
    Return tax information.
    """
    tax_obj = obj.Items()
    return tax_obj.list_items(parameters={'name': tax})

def get_tax_rates(books_name):
    """
    Get all tax rates.
    """
    taxes = TaxVariable.objects.values('dried_flower_tax_item','dried_leaf_tax_item')[0]
    books_obj = get_books_obj(books_name)
    response = dict()
    for k,v in taxes.items():
        item = get_tax(books_obj, v)['response'][0]
        response[item['name']] = item['rate']
    return response

def get_transportation_fees(books_name, name=None):
    """
    Return transportation fees.
    """
    obj = get_books_obj(books_name)
    if name:
        return get_tax(obj, name)
    return get_tax(obj, TRANSPORTATION_FEES)

def calculate_tax(books_name, product_category, quantity):
    """
    Calculate tax from product category for estimate page.
    """
    CAT_TAX_ITEM_FIELD = {
        'Flower':      'dried_flower_tax_item',
        'Trim':        'dried_leaf_tax_item',
        'fresh_plant': 'fresh_plant_tax_item',
    }
    taxes = TaxVariable.objects.values(*CAT_TAX_ITEM_FIELD.values())[0]
    books_obj = get_books_obj(books_name)
    if product_category not in CAT_TAX_ITEM_FIELD.keys():
        return {'status_code': 400,
                'error': 'product category not found.'}
    else:
        tax_item_name = taxes[CAT_TAX_ITEM_FIELD[product_category]]
        if not tax_item_name:
            return {'status_code': 400,
                    "error": f"Tax variable '{CAT_TAX_ITEM_FIELD[product_category]}' not defined."}
        item = get_tax(books_obj, tax_item_name)['response'][0]
        item_name = item['name']
        item_id = item['item_id']
        item_sku = item['sku']
        tax = item['rate']
        total_tax = float(quantity) * float(tax)

    return {
        'status_code': 200,
        'response': {
            'item_name': item_name,
            'total_tax': total_tax,
            'quantity': quantity,
            'item_id': item_id,
            'sku': item_sku,
            'rate': tax
        }
    }

def get_item(obj, data):
    """
    Return item from Zoho books with applied tax.
    """
    line_items = list()
    if not data.get('line_items'):
        return {"code": 1004, "data": data}
    for line_item in data.get('line_items'):
        item_obj = obj.Items()
        try:
            book_item = item_obj.list_items(parameters={'search_text': line_item['sku']})
            book_item = book_item['response']
        except KeyError:
            return {"code": 1003, "error": "Customer name not provided"}
        if len(book_item) == 1:
            book_item = book_item[0]
        elif len(book_item) > 1:
            for i in book_item:
                if i['sku'] == line_item['sku']:
                    book_item = i
                    break
        else:
            return {"code": 1003, "message": "Item not in zoho books."}
        item = get_item_dict(book_item, line_item)
        line_items.append(item)
    data['line_items'] = line_items
    return {"code": 0, "data": data}

def search_contact_by_field(contact_obj, field, value, contact_type):
    contact = None
    try:
        resp = contact_obj.list_contacts(parameters={field: value, 'contact_type': contact_type})
        contacts = resp['response']
    except KeyError:
        return {"code": 1003, "error": f"{contact_type} name not provided"}
    if contacts and value:
        for i in contacts:
            if i.get(field, '') == value or i.get('custom_field_hash', {}).get(field, '') == value:
                if i['contact_type'] == contact_type:
                    contact = i
                    break
    return contact


def search_contact(books_obj, value, contact_type):
    contact_obj = books_obj.Contacts()
    contact = None
    for field in ('contact_name', 'cf_legal_business_name', 'company_name',):
        contact = search_contact_by_field(contact_obj, field, value, contact_type)
        if contact:
            break
    return contact

def get_customer_id(obj, customer_name):
    """
    Return customer from Zoho books using Zoho Inventory name.
    """
    customer = search_contact_by_field(obj, 'contact_name', value=customer_name, contact_type='customer')
    if customer and customer.get('contact_id'):
        return customer['contact_id']


def get_vendor_id(obj, vendor_name):
    """
    Return vendor from Zoho books using Zoho Inventory name.
    """
    vendor = search_contact_by_field(obj, 'contact_name', value=vendor_name, contact_type='vendor')
    if vendor and vendor.get('contact_id'):
        return  vendor.get('contact_id')

def create_estimate(books_name, data, params=None):
    """
    Create estimate in Zoho Books.
    """
    try:
        obj = get_books_obj(books_name)
        estimate_obj = obj.Estimates()

        if not data.get('customer_id') and data.get('customer_name'):
            customer_id = get_customer_id(obj, data.get('customer_name'))
            if not customer_id:
                return {"code": 1003, "message": f"Customer \'{data.get('customer_name')}\' not in zoho books."}
            else:
                data['customer_id'] = customer_id

        if not data.get('customer_id'):
            return {"code": 1003, "message": f"customer_id is required."}

        result = get_item(obj, data)
        if result['code'] != 0:
           return result
        return estimate_obj.create_estimate(result['data'], parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def delete_estimate(books_name, estimate_id, params=None):
    """
    Delete an estimate in Zoho Books.
    """
    try:
        obj = get_books_obj(books_name)
        estimate_obj = obj.Estimates()
        return estimate_obj.delete_estimate(estimate_id=estimate_id, parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def update_estimate(books_name, estimate_id, data, params=None):
    """
    Update an estimate in Zoho Books.
    """
    try:
        obj = get_books_obj(books_name)
        estimate_obj = obj.Estimates()

        if not data.get('customer_id') and data.get('customer_name'):
            customer_id = get_customer_id(obj, data.get('customer_name'))
            if not customer_id:
                return {"code": 1003, "message": f"Customer \'{data.get('customer_name')}\' not in zoho books."}
            else:
                data['customer_id'] = customer_id

        result = get_item(obj, data)
        if result['code'] != 0 and result['code'] != 1004:
           return result
        return estimate_obj.update_estimate(estimate_id, result['data'], parameters=params)
    except Exception as exc:
        print(exc)
        return {
            'status_code': 400,
            'error': exc
        }
        
def get_estimate(books_name, estimate_id, params=None):
    """
    Get an estimate.
    """
    obj = get_books_obj(books_name)
    estimate_obj = obj.Estimates()
    return estimate_obj.get_estimate(estimate_id, parameters=params)

def list_estimates(books_name, params=None):
    """
    List estimates.
    """
    obj = get_books_obj(books_name)
    estimate_obj = obj.Estimates()
    return estimate_obj.list_estimates(parameters=params)

def update_estimate_address(books_name, estimate_id, address_type, data, params=None):
    """
    Update estimate address in zoho books.
    """
    obj = get_books_obj(books_name)
    estimate_obj = obj.Estimates()
    return estimate_obj.update_estimate_address(estimate_id, address_type, data, parameters=params)

def send_estimate_to_sign(books_name, estimate_id, contact_id=None, customer_name=None, notify_addresses=None):
    """
    sync estimate status from zoho books.
    """
    try:
        obj = get_books_obj(books_name)
        contact_obj = obj.Contacts()
        contact = None
        if contact_id:
            r = get_contact(books_name, contact_id)
            if r.get('contact_id'):
                contact = r
        if not contact and customer_name:
            contact = search_contact_by_field(contact_obj, 'contact_name', customer_name, contact_type='customer')
        # if contact.get('code'):
        if not contact:
            return {'code': '1003', 'error': 'Contact not found in zoho books.'}
        # contact_id = contact['contact_id']
        file_obj = get_estimate(books_name, estimate_id=estimate_id, params={'accept': 'pdf'})
        file_name = (file_obj['Content-Disposition'].split(';')[1]).split('=')[1].strip('"')
        file_binary = BytesIO(base64.b64decode(file_obj['data']))
        file_type = 'application/pdf'
        file_obj = [[file_name, file_binary, file_type]]
        if not contact.get('email'):
            return {'code': 1003, 'error': 'Contact doesnot have email in zoho books.'}
        customer_dict = [{'name': contact['contact_name'], 'email': contact['email']}]
        return submit_estimate(
            file_obj=file_obj,
            recipients=customer_dict,
            notes="",
            expiry=10,
            reminder_period=15,
            notify_addresses=notify_addresses
            )
    except KeyError as exc:
        print('Key not found', exc)
    except IndexError as exc:
        print('problem with file object', exc)
    except Exception as exc:
        print('error in sync estimate status', exc)

def mark_estimate(books_name, estimate_id, status, params=None):
    """
    Mark statement as sent, accepted, declined.
    """
    obj = get_books_obj(books_name)
    estimate_obj = obj.Estimates()
    return estimate_obj.mark_as(estimate_id, status, parameters=params)

def approve_estimate(books_name, estimate_id, params=None):
    """
    Approve estimate.
    """
    obj = get_books_obj(books_name)
    estimate_obj = obj.Estimates()
    return estimate_obj.approve_estimate(estimate_id, parameters=params)

def create_sales_order(books_name, record, params=None):
    """
    Create sales order.
    """
    try:
        obj = get_books_obj(books_name)
        so_obj = obj.SalesOrders()
        return so_obj.create_sales_order(record, parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def update_sales_order(books_name, salesorder_id, data, params=None):
    """
    Update purchase order to Zoho books.
    """
    try:
        obj = get_books_obj(books_name)
        so_obj = obj.SalesOrders()
        return so_obj.update_sales_order(salesorder_id, data, parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def mark_salesorder(books_name, so_id, status, params=None):
    """
    Mark statement.
    """
    obj = get_books_obj(books_name)
    so_obj = obj.SalesOrders()
    return so_obj.mark_as(so_id, status, parameters=params)

def approve_salesorder(books_name, so_id, params=None):
    """
    Approve salesorder.
    """
    obj = get_books_obj(books_name)
    so_obj = obj.SalesOrders()
    return so_obj.approve_sales_order(so_id, parameters=params)

def mark_purchaseorder(books_name, po_id, status, params=None):
    """
    Mark statement.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.PurchaseOrders()
    return po_obj.mark_as(po_id, status, parameters=params)

def approve_purchaseorder(books_name, po_id, params=None):
    """
    Approve purchase order.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.SalesOrders()
    return po_obj.approve_purchase_order(po_id, parameters=params)

def create_invoice(books_name, record, params=None):
    """
    Create invoice.
    """
    try:
        obj = get_books_obj(books_name)
        so_obj = obj.Invoices()
        return so_obj.create_invoice(record, parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def update_invoice(books_name, invoice_id, data, params=None):
    """
    Update purchase order to Zoho books.
    """
    try:
        obj = get_books_obj(books_name)
        invoice_obj = obj.Invoices()
        return invoice_obj.update_invoice(invoice_id, data, parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def mark_invoice(books_name, invoice_id, status, params=None):
    """
    Mark statement.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.Invoices()
    return invoice_obj.mark_as(invoice_id, status, parameters=params)

def approve_invoice(books_name, invoice_id, params=None):
    """
    Approve invoice.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.Invoices()
    return invoice_obj.approve_invoice(invoice_id, parameters=params)

def mark_bill(books_name, bill_id, status, params=None):
    """
    Mark statement.
    """
    obj = get_books_obj(books_name)
    bill_obj = obj.Bills()
    return bill_obj.mark_as(bill_id, status, parameters=params)

def approve_bill(books_name, bill_id, params=None):
    """
    Approve bill.
    """
    obj = get_books_obj(books_name)
    bill_obj = obj.Bills()
    return bill_obj.approve_bill(bill_id, parameters=params)

def list_contacts(books_name, params=None):
    """
    List contact.
    """
    def _list(books_name):
        obj = get_books_obj(books_name)
        contact_obj = obj.Contacts()
        return contact_obj.list_contacts(parameters=params)
    
    if books_name == 'all':
        result = dict()
        for org in BOOKS_ORGANIZATION_LIST:
            result[org] = _list(org)
        return result
    else:
        return _list(books_name)


def get_purchase_order(books_name, po_id, params=None):
    """
    Get specific purchase order.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.PurchaseOrders()
    return po_obj.get_purchase_order(po_id=po_id, parameters=params)

def create_purchase_order(books_name, record, params=None):
    """
    Create purchase order to Zoho books.
    """
    try:
        obj = get_books_obj(books_name)
        po_obj = obj.PurchaseOrders()

        if not record.get('vendor_id') and record.get('vendor_name'):
            vendor_id = get_vendor_id(obj, record.get('vendor_name'))
            if not vendor_id:
                return {"code": 1003, "message": f"Vendor \'{record.get('vendor_name')}\' not in zoho books."}
            else:
                record['vendor_id'] = vendor_id

        if not record.get('vendor_id'):
            return {"code": 1003, "message": f"vendor_id is required."}


        result = get_item(obj, record)
        if result['code'] != 0:
           return result
        return po_obj.create_purchase_order(result['data'], parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def update_purchase_order(books_name, po_id, record, params=None):
    """
    Update purchase order to Zoho books.
    """
    try:
        obj = get_books_obj(books_name)
        po_obj = obj.PurchaseOrders()

        if not record.get('vendor_id') and record.get('vendor_name'):
            vendor_id = get_vendor_id(obj, record.get('vendor_name'))
            if not vendor_id:
                return {"code": 1003, "message": f"Vendor \'{record.get('vendor_name')}\' not in zoho books."}
            else:
                record['vendor_id'] = vendor_id

        result = get_item(obj, record)
        if result['code'] != 0 and result['code'] != 1004:
           return result
        return po_obj.update_purchase_order(po_id, result['data'], parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def submit_purchase_order(books_name, po_id, params=None):
    """
    Submit specific purchase order.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.PurchaseOrders()
    return po_obj.submit_purchase_order(po_id=po_id, parameters=params)

def list_purchase_orders(books_name, params=None):
    """
    List specific purchase order.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.PurchaseOrders()

    legal_business_name = params.get('vendor_name')
    contact_obj = obj.Contacts()
    contacts = contact_obj.list_contacts({'cf_legal_business_name': legal_business_name})
    for contact in contacts['response']:
        if contact['company_name'] == legal_business_name and contact['contact_type'] == 'vendor':
            params['vendor_name'] = contact['contact_name']
            break

    return po_obj.list_purchase_orders(parameters=params)


def get_vendor_payment(books_name, payment_id, params={}):
    """
    Return vendor payments made.
    """
    obj = get_books_obj(books_name)
    vp_obj = obj.VendorPayments()
    return vp_obj.get_payment(payment_id=payment_id, parameters=params)

def list_vendor_payments(books_name, params=None):
    """
    List vendor payments.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.VendorPayments()
    legal_business_name = params.get('vendor_name')
    if legal_business_name:
        contact_obj = obj.Contacts()
        contacts = contact_obj.list_contacts({'cf_legal_business_name': legal_business_name})
        for contact in contacts['response']:
            if contact['company_name'] == legal_business_name and contact['contact_type'] == 'vendor':
                params['vendor_name'] = contact['contact_name']
                break
    payments = po_obj.list_payments(parameters=params)
    for payment in payments.get('response'):
        data = get_vendor_payment(books_name, payment['payment_id'])
        payment['balance'] = 0
        for record in data.get('bills'):
            payment['balance'] += record['balance']
    return payments


def get_customer_payment(books_name, payment_id, params={}):
    """
    Return customer payments made.
    """
    obj = get_books_obj(books_name)
    vp_obj = obj.CustomerPayments()
    return vp_obj.get_payment(payment_id=payment_id, parameters=params)

def get_payment_from_redis(books_name, payment_id):
    """
    Get invoices data from redis.
    """
    r = redis.from_url(REDIS_URL)
    if r.get(payment_id):
        return json.loads(r.get(payment_id))
    else:
        resp = get_customer_payment(books_name, payment_id, params={})
        r.set(payment_id, json.dumps(resp))
        return resp

def list_customer_payments(books_name, params=None):
    """
    List customer payments.
    """
    obj = get_books_obj(books_name)
    po_obj = obj.CustomerPayments()
    payments = po_obj.list_payments(parameters=params)
    for payment in payments.get('response'):
        data = get_payment_from_redis(books_name, payment['payment_id'])
        payment['balance'] = 0
        for record in data.get('invoices'):
            payment['balance'] += record['balance']
    return payments

def get_invoice(books_name, invoice_id, params=None):
    """
    Get an invoice.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.Invoices()
    return invoice_obj.get_invoice(invoice_id=invoice_id, parameters=params)

def list_invoices(books_name, params=None):
    """
    List invoices.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.Invoices()
    return invoice_obj.list_invoices(parameters=params)

def get_vendor_credit(books_name, credit_id, params=None):
    """
    Get vendor credit.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.VendorCredits()
    return invoice_obj.get_vendor_credit(credit_id=credit_id, parameters=params)

def list_vendor_credits(books_name, params=None):
    """
    List vendor credits.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.VendorCredits()
    return invoice_obj.list_vendor_credits(parameters=params)

    # if books_name == 'all':
    #     result = dict()
    #     for org in BOOKS_ORGANIZATION_LIST:
    #         result[org] = _list(org)
    #     return result
    # else:
    #     return _list(books_name)

def get_unpaid_bills(books_name, vendor, status='unpaid', start_date=None, end_date=None):
    """
    Return total unpaid bills.
    """
    response = list_bills(books_name, {
        'vendor_name': vendor,
        'status': status,
        'date_start': start_date,
        'date_end': end_date})
    response = response.get('response', [])
    unpaid = sum([i['balance'] for i in response])
    return unpaid

def get_available_credit(books_name, vendor, status='open'):
    """
    Get available vendor credits.
    """
    response = list_vendor_credits(books_name, {
        'vendor_name': vendor,
        'status':status})
    response = response.get('response', [])
    credits = sum([i['total'] for i in response])
    return credits

def get_unpaid_invoices(books_name, customer, status='unpaid'):
    """
    Return outstanding invoices.
    """
    response = list_invoices(books_name, {
        'customer_name': customer,
        'status': status})
    response = response.get('response', [])
    unpaid = sum([i['balance'] for i in response])
    return unpaid

def get_invoice_from_redis(books_name, invoice_id):
    """
    Get invoices data from redis.
    """
    r = redis.from_url(REDIS_URL)
    if r.get(invoice_id):
        return json.loads(r.get(invoice_id))
    else:
        resp = get_invoice(books_name, invoice_id, params={})
        r.set(invoice_id, json.dumps(resp))
        return resp

def get_buyer_summary(books_name,customer):
    """
    Get buyer summary for books.
    """
    def _buyer_summary(books_name, customer):
        if not customer:
            return {
                "total_invoice_price": 0,
                "total_quantity": 0,
                "average_invoice_price": 0,
                "outstanding_bills": 0,
                "category_count": 0,
                "category_percentage": 0
            }
        total_quantity = 0
        total_items = 0
        category_percentage = category_count = {
            'flower': 0,
            'trim': 0,
            'smalls': 0
        }
        start_date = datetime.now().date().replace(month=1, day=1)
        end_date = datetime.now().date()
        invoices = list_invoices(books_name, params={'customer_name': customer,
            'date_start': start_date,
            'date_end': end_date})
        invoices = invoices.get('response', [])
        invoices_count = len(invoices)
        invoices_total = sum([i['total'] for i in invoices])
        for invoice in invoices:
            resp = get_invoice_from_redis(books_name, invoice.get('invoice_id'))
            for item in resp['line_items']:
                if 'Cultivation Tax' in item.get('name') or 'MCSP' in item.get('name'):
                    continue
                total_quantity += item['quantity']
                try:
                    inventory = Inventory.objects.filter(sku=item['sku']).latest('last_modified_time')
                except Inventory.DoesNotExist:
                    continue
                try:
                    total_items += 1
                    if 'Flower' in inventory.category_name:
                        category_count['flower'] += 1
                    elif 'Trim' in inventory.category_name:
                        category_count['trim'] += 1
                    elif 'Smalls' in inventory.category_name:
                        category_count['smalls'] += 1
                except AttributeError as exc:
                    continue
        if total_items:
            for k, v in category_count.items():
                category_percentage[k] = (v/total_items) * 100
        return {
            "total_invoice_price": invoices_total,
            "total_quantity": total_quantity,
            "average_invoice_price": invoices_total/invoices_count if invoices_count else 0,
            "outstanding_bills": get_unpaid_bills(books_name, customer, status='unpaid', start_date=start_date, end_date=end_date),
            "category_count": category_count,
            "category_percentage": category_percentage
            }

    if books_name == 'all':
        result = dict()
        for org in BOOKS_ORGANIZATION_LIST:
            result[org] = _buyer_summary(org, customer)
        return result
    else:
        return _buyer_summary(books_name, customer)

def get_contact_statement(books_name, contact_id):
    """
    Get contact address list.
    """
    obj = get_books_obj(books_name)
    contact_obj = obj.Contacts()
    return contact_obj.get_statement(contact_id)

# def create_purchase_order(books_name, data, params=None):
#     """
#     Create purchase order in Zoho Books.
#     """
#     obj = get_books_obj(books_name)
#     po_obj = obj.PurchaseOrders()
#     result = get_customer(obj, data)
#     if result['code'] != 0:
#         return result
#     result = get_item(obj, result['data'])
#     if result['code'] != 0:
#         return result
#     return po_obj.create_purchase_order(result['data'], parameters=params)

def get_bill(books_name, bill_id, params=None):
    """
    Get a bill.
    """
    obj = get_books_obj(books_name)
    bill_obj = obj.Bills()
    return bill_obj.get_bill(bill_id=bill_id, parameters=params)

def list_bills(books_name, params=None):
    """
    List bills.
    """
    obj = get_books_obj(books_name)
    bill_obj = obj.Bills()
    contact_obj = obj.Contacts()
    legal_business_name = params.get('vendor_name')
    contacts = contact_obj.list_contacts({'cf_legal_business_name': legal_business_name})
    for contact in contacts['response']:
        if contact['company_name'] == legal_business_name and contact['contact_type'] == 'vendor':
            params['vendor_name'] = contact['contact_name']
            break
    return bill_obj.list_bills(parameters=params)


def get_salesorder(books_name, so_id, params=None):
    """
    Get sales order
    """
    obj = get_books_obj(books_name)
    bill_obj = obj.SalesOrders()
    return bill_obj.get_sales_order(so_id=so_id, parameters=params)

def list_salesorders(books_name, params=None):
    """
    List sales orders
    """
    obj = get_books_obj(books_name)
    bill_obj = obj.SalesOrders()
    return bill_obj.list_sales_orders(parameters=params)

def get_sub_statuses(books_name, params=None):
    """
    Get sub-statuses.
    """
    obj = get_books_obj(books_name)
    invoice_obj = obj.SalesOrders()
    return invoice_obj.get_sub_statuses(parameters=params)

def get(record, v, **kwargs):
    """
    Return value from record.
    """
    value = record.get(v, None)
    if v == 'line_items':
        if kwargs.get('line_item_parser') == 'salesorder_parser':
            line_item = parse_book_object('salesorder_line_item', value)
            return line_item    
        elif kwargs.get('line_item_parser') == 'salesorder_to_invoice_parser':
            line_item = parse_book_object('salesorder_to_invoice_line_item', value)
            return line_item    
        line_item = parse_book_object('item', value)
        return line_item
    if v == 'custom_fields':
        custom_fields = parse_book_object('custom_fields', value)
        return custom_fields
    return value

def parse_book_object(module, record, **kwargs):
    """
    Parser for books objects.
    """
    if isinstance(record, list):
        result = list()
        for obj in record:
            result.append({k:get(obj, v, **kwargs) for k, v in BOOKS_FORMAT_DICT[module].items() if get(obj, v) != None})
        return result
    return {k:get(record, v, **kwargs) for k, v in BOOKS_FORMAT_DICT[module].items() if get(record, v) != None}

def get_zoho_user_permission(books_name='books_efd', user_email=None):
    """
    Return zoho user permissions.
    """
    if user_email:
        obj = get_books_obj(books_name)
        user_obj = obj.Users()
        role_obj = obj.Roles()
        user = user_obj.list_users({"email": user_email})
        if user.get('response'):
            user = user.get('response')[0]
            user['permissions'] = role_obj.get_role(user.get('role_id'))
        return user
    return None
