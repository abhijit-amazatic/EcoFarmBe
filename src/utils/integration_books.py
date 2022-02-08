import queue
import time
import math
from integration.books import (get_books_obj,)


def trigger_estimate_update_workflow(books_name):
    book_obj = get_books_obj(books_name)
    estimate_obj = book_obj.Estimates()
    estimates_response = {}
    total_pages = math.inf
    page = 1
    while(page < total_pages):
        estimates_response = estimate_obj.list_estimates(parameters={'page': page, 'per_page':2})
        if not estimates_response.get('code'):
            total = estimates_response['page_context']['total']
            total_pages = estimates_response['page_context']['total_pages']
            per_page = estimates_response['page_context']['per_page']
            page = estimates_response['page_context']['page']
            for i, estimate in enumerate(estimates_response['response']):
                time.sleep(2)
                item_number = per_page*(page-1)+i+1
                res = estimate_obj.update_estimate(estimate['estimate_id'], {'id':estimate['estimate_id']}, parameters={})
                if not res.get('code'):
                    print(f"{item_number}/{total}: {estimate['estimate_id']} OK")
                else:
                    print(f"{item_number}/{total}: {estimate['estimate_id']} {res}")
            page += 1
        else:
            print(estimates_response)
            break

def trigger_salesorder_update_workflow(books_name):
    book_obj = get_books_obj(books_name)
    so_obj = book_obj.SalesOrders()
    salesorders_response = {}
    total_pages = math.inf
    page = 1
    while(page < total_pages):
        salesorders_response = so_obj.list_sales_orders(parameters={'page': page, 'per_page':2})
        if not salesorders_response.get('code'):
            total = salesorders_response['page_context']['total']
            total_pages = salesorders_response['page_context']['total_pages']
            per_page = salesorders_response['page_context']['per_page']
            page = salesorders_response['page_context']['page']
            for i, salesorder in enumerate(salesorders_response['response']):
                time.sleep(2)
                item_number = per_page*(page-1)+i+1
                res = so_obj.update_sales_order(salesorder['salesorder_id'], {'id':salesorder['salesorder_id']}, parameters={})
                if not res.get('code'):
                    print(f"{item_number}/{total}: {salesorder['salesorder_id']} OK")
                else:
                    print(f"{item_number}/{total}: {salesorder['salesorder_id']} {res}")
            page += 1
        else:
            print(salesorders_response)
            break

def trigger_invoice_update_workflow(books_name):
    book_obj = get_books_obj(books_name)
    invoice_obj = book_obj.Invoices()
    invoices_response = {}
    total_pages = math.inf
    page = 1
    while(page < total_pages):
        invoices_response = invoice_obj.list_invoices(parameters={'page': page, 'per_page':2})
        if not invoices_response.get('code'):
            total = invoices_response['page_context']['total']
            total_pages = invoices_response['page_context']['total_pages']
            per_page = invoices_response['page_context']['per_page']
            page = invoices_response['page_context']['page']
            for i, invoice in enumerate(invoices_response['response']):
                time.sleep(2)
                item_number = per_page*(page-1)+i+1
                res = invoice_obj.update_invoice(invoice['invoice_id'], {'id':invoice['invoice_id']}, parameters={})
                if not res.get('code'):
                    print(f"{item_number}/{total}: {invoice['invoice_id']} OK")
                else:
                    print(f"{item_number}/{total}: {invoice['invoice_id']} {res}")
            page += 1
        else:
            print(invoices_response)
            break
