"""
Integration views
"""
import json
from datetime import (datetime, timedelta)
from django.http import (QueryDict,)
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated,)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.authentication import (TokenAuthentication,)

from core.permissions import UserPermissions
from .models import Integration
from integration.box import(get_box_tokens, get_shared_link,)
from integration.inventory import (
    get_inventory_item, get_inventory_items,)
from integration.crm import (
    search_query, get_picklist,
    list_crm_contacts, create_lead,
    get_records_from_crm,get_accounts_from_crm,)
from integration.books import (
    create_contact, create_estimate,
    get_estimate, list_estimates,
    get_contact, list_contacts,
    get_purchase_order, list_purchase_orders,
    get_vendor_payment, list_vendor_payments,
    get_invoice, list_invoices,
    get_unpaid_invoices, get_vendor_credit,
    list_vendor_credits,get_available_credit,
    calculate_tax, get_tax_rates,
    update_estimate, delete_estimate,
    send_estimate_to_sign, get_contact_addresses,
    mark_estimate, send_estimate_to_sign)
from integration.tasks import (send_estimate, )

class GetBoxTokensView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)

class GetBoxSharedLink(APIView):
    """
    Get shared file link.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        try:
            file_id = request.query_params.get('id')
            expire_time = datetime.today() + timedelta(hours=1)
            response = get_shared_link(
                file_id,
                access="open",
                unshared_at=expire_time,
                allow_download=False)
            return Response({"status_code": 200,
                             "shared_link":response})
        except Exception as exc:
            return Response({
                "status_code": 400,
                "error": exc})

class SearchCultivars(APIView):
    """
    Return Cultivar information from Zoho CRM.
    """
    permission_class = (IsAuthenticated, )
    
    def get(self, request):
        """
        Get Cultivar information.
        """
        data = search_query('Cultivars', request.query_params['cultivar_name'], 'Name', True)
        if data['status_code'] == 200:
            return Response(data)
        return Response({})

class GetPickListView(APIView):
    """
    Get field dropdowns from Zoho CRM.
    """
    
    def get(self, request):
        """
        Get picklist.
        """
        return Response(get_picklist('Vendors', request.query_params['field']))

    def get_permissions(self):
        if self.request.query_params['field'] in ('Region', 'County'):
            self.permission_classes = [AllowAny, ]
        else:
            self.permission_classes = [IsAuthenticated, ]
        return super(GetPickListView, self).get_permissions()

class GetPickListAccountView(APIView):
    """
    Get field dropdowns from Zoho CRM accounts.
    """
    
    def get(self, request):
        """
        Get picklist.
        """
        return Response(get_picklist('Accounts', request.query_params['field']))

    def get_permissions(self):
        if self.request.query_params['field'] in ('Product of Interest',):
            self.permission_classes = [AllowAny, ]
        else:
            self.permission_classes = [IsAuthenticated, ]
        return super(GetPickListAccountView, self).get_permissions()

class CRMContactView(APIView):
    """
    Get Contacts from Zoho CRM.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contacts.
        """
        if request.query_params.get('contact_id'):
            return Response(list_crm_contacts(request.query_params.get('contact_id')))
        return Response(list_crm_contacts())

class CRMVendorView(APIView):
    """
    Get Vendor from Zoho CRM.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get vendor.
        """
        if request.query_params.get('legal_business_name'):
            return Response(get_records_from_crm(request.query_params.get('legal_business_name')))
        return Response({})

class InventoryView(APIView):
    """
    View class for Zoho inventory. Fetch data from Zoho Inventory.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get an item.
        """
        if request.query_params.get('item_id', None):
            item_id = request.query_params['item_id']
            return Response(get_inventory_item(item_id))
        data = get_inventory_items(params=request.query_params.dict())
        return Response(data)
    
class EstimateView(APIView):
    """
    View class for Zoho books estimates.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get estimates.
        """
        if request.query_params.get('estimate_id', None):
            return Response(get_estimate(
                request.query_params.get('estimate_id'),
                params=request.query_params.dict()))
        return Response(list_estimates(params=request.query_params.dict()))

    def post(self, request):
        """
        Create and estimate in Zoho Books.
        """
        is_draft = request.query_params.get('is_draft')
        if is_draft == 'true' or is_draft == 'True':
            response = create_estimate(data=request.data, params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response)
        estimate = create_estimate(data=request.data, params=request.query_params.dict())
        if estimate.get('code') and estimate['code'] != 0:
            return Response(estimate, status=status.HTTP_400_BAD_REQUEST)
        if estimate.get('estimate_id'):
            estimate_id = estimate['estimate_id']
            contact_id = estimate['customer_id']
            mark_estimate(estimate_id, 'sent')
            mark_estimate(estimate_id, 'accepted')
        return Response(estimate)

    def put(self, request):
        """
        Update an estimate in Zoho Books.
        """
        is_draft = request.query_params.get('is_draft')
        estimate_id = request.data['estimate_id']
        if is_draft == 'true' or is_draft == 'True':
            response = update_estimate(estimate_id=estimate_id, data=request.data, params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response)
        estimate = update_estimate(estimate_id=estimate_id, data=request.data, params=request.query_params.dict())
        if estimate.get('code') and estimate['code'] != 0:
            return Response(estimate, status=status.HTTP_400_BAD_REQUEST)
        if estimate.get('estimate_id'):
            estimate_id = estimate['estimate_id']
            contact_id = estimate['customer_id']
            mark_estimate(estimate_id, 'sent')
            mark_estimate(estimate_id, 'accepted')
        return Response(estimate)
    
    def delete(self, request):
        """
        Delete an estimate from Zoho books.
        """
        estimate_id = request.data['estimate_id']
        return Response(delete_estimate(estimate_id=estimate_id, params=request.query_params.dict()))

class EstimateSignView(APIView):
    """
    View class to sign for estimate.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get signing url.
        """
        estimate_id = request.query_params.get('estimate_id', None)
        customer_name = request.query_params.get('customer_name', None)
        if estimate_id and customer_name:
            return Response(send_estimate_to_sign(estimate_id, customer_name))
        return Response({})

class EstimateTaxView(APIView):
    """
    View class to calculate tax for estimate.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get estimates tax.
        """
        product_category = request.query_params.get('product_category', None)
        quantity = request.query_params.get('quantity', None)
        if product_category and quantity:
            return Response(calculate_tax(product_category, quantity))
        return Response({})

class EstimateStatusView(APIView):
    """
    View class to update status for estimate.
    """
    permission_classes = (IsAuthenticated,)
    
    def put(self, request):
        """
        Update status.
        """
        estimate_id = request.query_params.get('estimate_id', None)
        status = request.query_params.get('status', None)
        if estimate_id and status:
            return Response(mark_estimate(estimate_id, status))
        return Response({})

class PurchaseOrderView(APIView):
    """
    View class for Zoho books purchase orders.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get PO.
        """
        if request.query_params.get('po_id', None):
            return Response(get_purchase_order(
                request.query_params.get('po_id'),
                params=request.query_params.dict()))
        return Response(list_purchase_orders(params=request.query_params.dict()))

class VendorPaymentView(APIView):
    """
    View class for Zoho books vendor payments.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get PO.
        """
        if request.query_params.get('payment_id', None):
            return Response(get_vendor_payment(
                request.query_params.get('payment_id'),
                params=request.query_params.dict()))
        return Response(list_vendor_payments(params=request.query_params.dict()))

class InvoiceView(APIView):
    """
    View class for Zoho books invoices.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get an invoice.
        """
        if request.query_params.get('invoice_id', None):
            return Response(get_invoice(
                request.query_params.get('invoice_id'),
                params=request.query_params.dict()))
        return Response(list_invoices(params=request.query_params.dict()))

class VendorCreditView(APIView):
    """
    View class for Zoho books vendor credit.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get vendor credit.
        """
        if request.query_params.get('credit_id', None):
            return Response(get_vendor_credit(
                request.query_params.get('credit_id'),
                params=request.query_params.dict()))
        return Response(list_vendor_credits(params=request.query_params.dict()))

class AccountSummaryView(APIView):
    """
    View class for Zoho books summary.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get account summary.
        """
        vendor = request.query_params.get('vendor_name')
        total_unpaid_invoices = get_unpaid_invoices(vendor)
        total_credits = get_available_credit(vendor)
        return Response({
            "Available_Credits": total_credits,
            "Overdue_Invoices": total_unpaid_invoices
            })

class ContactView(APIView):
    """
    View class for Zoho books contacts.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contact.
        """
        if request.query_params.get('contact_id', None):
            return Response(get_contact(request.query_params.get('contact_id')))
        return Response(list_contacts(params=request.query_params.dict()))

    def post(self, request):
        """
        Create contact in Zoho Books.
        """
        return Response(create_contact(data=request.data, params=request.query_params.dict()))

class ContactAddressView(APIView):
    """
    View class for Zoho books contacts address.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contact addresses.
        """
        if request.query_params.get('contact_name', None):
            return Response(get_contact_addresses(request.query_params.get('contact_name')))
        return Response({'error': 'Conact name not specified'})

class LeadView(APIView):
    """
    View class for Zoho CRM Leads.
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Create Leads.
        """
        return Response(create_lead(record=request.data))

class LeadSourcesView(APIView):
    """
    View class for Zoho CRM Leads.
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """
        Get lead sources list.
        """
        return Response(get_picklist('Leads', 'Lead Source'))

class GetTaxView(APIView):
    """
    View class to get tax.
    """
    authentication_classes = (TokenAuthentication, )
    
    def get(self, request):
        """
        Get tax.
        """
        return Response(get_tax_rates())

class EstimateApproveView(APIView):
    """
    View class to sync estimate status from zoho books.
    """
    authentication_classes = (TokenAuthentication, )
    
    def post(self, request):
        """
        sync status from zoho books.
        """
        record = send_estimate_to_sign(request.data)
        return Response(record)


class ClientCodeView(APIView):
    """
    Account's client code view
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get accounts client code.
        """
        if request.query_params.get('legal_business_name'):
            account_data = get_accounts_from_crm(request.query_params.get('legal_business_name'))
            return Response({"client_code":account_data.get('basic_profile',{}).get('client_code')})
        return Response({'error': 'Something went wrong!'})    

    
