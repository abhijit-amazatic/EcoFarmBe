"""
Integration views
"""
from datetime import (datetime, timedelta)
import base64
from django.http import (QueryDict,)
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated,)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import (permissions, viewsets, filters, mixins)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView
from rest_framework.authentication import (TokenAuthentication,)
from django.conf import settings

from core.permissions import UserPermissions
from .models import (Integration,OrderVariable)
from integration.box import(
    get_box_tokens, get_shared_link,
    get_client_folder_id, create_folder, get_download_url)
from integration.inventory import (
    get_inventory_item, get_inventory_items,)
from integration.crm import (
    search_query, get_picklist,
    list_crm_contacts, create_lead,
    get_records_from_crm,
    get_accounts_from_crm,
    get_vendors_from_crm,
    get_record, update_vendor_tier,
)
from integration.books import (
    create_contact, create_estimate,
    get_estimate, list_estimates,
    get_contact, list_contacts,
    get_purchase_order, list_purchase_orders,
    get_vendor_payment, list_vendor_payments,
    get_invoice, list_invoices,
    get_unpaid_bills, get_vendor_credit,
    list_vendor_credits,get_available_credit,
    calculate_tax, get_tax_rates,
    update_estimate, delete_estimate,
    send_estimate_to_sign, get_contact_addresses,
    mark_estimate, get_transportation_fees,
    get_customer_payment, list_customer_payments,
    get_bill, list_bills,get_salesorder,
    list_salesorders, update_estimate_address,
    add_contact_address, edit_contact_address,
    get_contact_person, list_contact_persons,
    create_contact_person, update_contact_person,
    get_unpaid_invoices)
from integration.sign import (upload_pdf_box, get_document,
                              get_embedded_url_from_sign,
                              download_pdf,
                              send_template)
from integration.tasks import (send_estimate, )
from integration.utils import (get_distance, get_places)
from .serializers import OrderVariableSerializer
from core.settings import (INVENTORY_BOX_ID, BOX_CLIENT_ID,
                           BOX_CLIENT_SECRET,
    )
from slacker import Slacker
from core.mailer import (mail, mail_send,)
from integration.apps.scrapper import (Scrapper, )
from labtest.models import (LabTest,)

slack = Slacker(settings.SLACK_TOKEN)

class GetBoxTokensView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        tokens = get_box_tokens()
        return Response(tokens)

class GetBoxTokenAuthenticationView(APIView):
    """
    Return Access and Refresh Tokens for Box.
    """
    authentication_classes = (TokenAuthentication, )

    def get(self, request):
        tokens = get_box_tokens()
        tokens['BOX_CLIENT_ID'] = BOX_CLIENT_ID
        tokens['BOX_CLIENT_SECRET'] = BOX_CLIENT_SECRET
        tokens['inventory_folder_id'] = INVENTORY_BOX_ID
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
                "error": exc}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class GetRecordView(APIView):
    """
    Return record from crm.
    """
    permission_class = (IsAuthenticated, )
    
    def get(self, request):
        """
        Get recrod.
        """
        module = request.query_params.get('module')
        record_id = request.query_params.get('id')
        legal_business_name = request.query_params.get('legal_business_name')
        if module and record_id:
            record = get_record(module, record_id)
            if record['status_code'] == 200:
                return Response(record, status=status.HTTP_200_OK)
            return Response(record, status=status.HTTP_400_BAD_REQUEST)
        elif module and legal_business_name:
            record = search_query('Accounts', legal_business_name, 'Account_Business_DBA')
            if record['status_code'] == 200:
                return Response(record, status=status.HTTP_200_OK)
            return Response(record, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class GetPickListView(APIView):
    """
    Get field dropdowns from Zoho CRM.
    """
    
    def get(self, request):
        """
        Get picklist.
        """
        if request.query_params.get('module') == 'Brands':
            return Response(get_picklist('Brands', request.query_params['field']))
        if request.query_params.get('module') == 'Orgs':
            return Response(get_picklist('Orgs', request.query_params['field']))
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
        elif request.query_params.get('vendor_name'):
            record_name = request.query_params.get('vendor_name')
            response = search_query('Vendors', record_name, 'Vendor_Name', True)
            return Response(response)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

class CRMVendorTierView(APIView):
    """
    Update Tier selection in Zoho CRM Vendor module.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Update vendor tier field.
        """
        id = request.data.get('id', None)
        if id and request.data.get('program_selection'):
            response = update_vendor_tier('Vendors', request.data)
            if response.get('code') == 0:
                return Response(response, status=status.HTTP_202_ACCEPTED)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
            
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
        else:
            estimate = create_estimate(data=request.data, params=request.query_params.dict())
            if estimate.get('code') and estimate['code'] != 0:
                return Response(estimate, status=status.HTTP_400_BAD_REQUEST)
            # if estimate.get('estimate_id'):
            #     estimate_id = estimate['estimate_id']
            #     contact_id = estimate['customer_id']
            #     mark_estimate(estimate_id, 'sent')
            #     mark_estimate(estimate_id, 'accepted')
            return Response(estimate)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

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
        else:
            estimate = update_estimate(estimate_id=estimate_id, data=request.data, params=request.query_params.dict())
            if estimate.get('code') and estimate['code'] != 0:
                return Response(estimate, status=status.HTTP_400_BAD_REQUEST)
            # if estimate.get('estimate_id'):
            #     estimate_id = estimate['estimate_id']
            #     contact_id = estimate['customer_id']
            #     mark_estimate(estimate_id, 'sent')
            #     mark_estimate(estimate_id, 'accepted')
            return Response(estimate)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """
        Delete an estimate from Zoho books.
        """
        estimate_id = request.data['estimate_id']
        if estimate_id:
            return Response(delete_estimate(estimate_id=estimate_id, params=request.query_params.dict()))
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class EstimateAddressView(APIView):
    """
    View class to sign for estimate.
    """
    permission_classes = (IsAuthenticated,)
    
    def put(self, request):
        """
        Update estimate address.
        """
        estimate_id = request.data.get('estimate_id', None)
        address_type = request.data.get('address_type', None)
        if estimate_id and address_type:
            response = update_estimate_address(estimate_id, address_type, request.data)
            if response.get('code') and response.get('code') != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


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
            response = send_estimate_to_sign(estimate_id, customer_name)
            if response.get('code') and response.get('code') != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class TemplateSignView(APIView):
    """
    View class to sign for template.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Get template signing url.
        """
        template_id = request.data.get('template_id', None)
        recipient = request.data.get('recipient', None)
        licenses = request.data.get('licenses', None)
        legal_business_names = request.data.get('legal_business_names', None)
        EIN = request.data.get('EIN', None)
        SSN = request.data.get('SSN', None)
        business_structure = request.data.get('business_structure', None)
        license_owner_name = request.data.get('license_owner_name', None)
        premise_address = request.data.get('premise_address', None)
        premise_state = request.data.get('premise_state', None)
        premise_city = request.data.get('premise_city', None)
        premise_zip = request.data.get('premise_zip', None)
        license_owner_email = request.data.get('license_owner_email', None)

        if template_id and recipient:
            return Response(send_template(template_id,
                                          recipient,
                                          licenses,
                                          legal_business_names,
                                          EIN, SSN, business_structure,
                                          license_owner_name, premise_address,
                                          premise_state, premise_city, premise_zip,
                                          license_owner_email
                                          ))
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class DownloadSignDocumentView(APIView):
    """
    View class to download sign document.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get document binary.
        """
        response = list()
        request_id = request.query_params.get('request_id')
        business_dba = request.query_params.get('business_dba')
        document_number = request.query_params.get('document_number')
        if request_id and business_dba and document_number:
            dir_name = f'{business_dba}_{document_number}'
            data = get_document(request_id)['requests']
            folder_id = get_client_folder_id(dir_name)
            new_folder = create_folder(folder_id, 'agreements')
            for document in data.get('document_ids'):
                filename = 'unsigned-' + document.get('document_name')
                file_id = upload_pdf_box(request_id, new_folder, filename, True)
                response.append(get_download_url(file_id))
        return Response(response)

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
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class EstimateSignCompleteView(APIView):
    """
    View class for sign completed.
    """
    permission_classess = (IsAuthenticated, )
    
    def post(self, request):
        """
        Post data from zoho sign on sign.
        """
        request_id = request.data.get('request_id')
        estimate_id = request.data.get('estimate_id')
        business_dba = request.data.get('business_dba')
        document_number = request.data.get('document_number')
        order_number = request.data.get('order_number')
        dir_name = f'{business_dba}_{document_number}'
        is_agreement = request.data.get('is_agreement')
        data = get_document(request_id)['requests']
        response = list()
        for document in data.get('document_ids'):
            filename = document.get('document_name')
            folder_id = get_client_folder_id(dir_name)
            if is_agreement:
                new_folder = create_folder(folder_id, 'agreements')
            else:
                a = mark_estimate(estimate_id, 'sent')
                a = mark_estimate(estimate_id, 'accepted')
                new_folder = create_folder(folder_id, 'estimates')
            response.append(upload_pdf_box(request_id, new_folder, filename, is_agreement))
        if order_number:    
            mail("order.html",{'link': settings.FRONTEND_DOMAIN_NAME+'login','full_name': request.user.full_name,'order_number':order_number,'business_name': business_dba, 'license_number': document_number},"Your Thrive Society Order %s." %order_number, request.user.email,file_data=download_pdf(request_id))   
        return Response(response)

class GetTemplateStatus(APIView):
    """
    View class to get Zoho sign template status.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """
        Get Zoho sign document status.
        """
        request_id = request.query_params.get('request_id')
        recipient_email = request.query_params.get('recipient_email')
        if request_id:
            response = get_document(request_id)
            status_ = response['requests']['request_status']
            actions = response['requests']['actions']
            for action in actions:
                if action['recipient_email'] == recipient_email:
                    if action['action_status'] == 'SIGNED':
                        is_signed = True
                        break
                    else:
                        is_signed = False
                        break
            if response['code'] == 0:
                return Response({
                    'code': 0,
                    'status': status_,
                    'is_singed_by_user': is_signed})
            else:
                return Response({'code': 1, 'error': 'Incorrect request id or Document not in Zoho sign'},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response({'code': 1, 'error': 'No request id provided.'}, status=status.HTTP_400_BAD_REQUEST)


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
        Get payment made.
        """
        if request.query_params.get('payment_id', None):
            return Response(get_vendor_payment(
                request.query_params.get('payment_id'),
                params=request.query_params.dict()))
        return Response(list_vendor_payments(params=request.query_params.dict()))

class CustomerPaymentView(APIView):
    """
    View class for Zoho books customer payments received.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get Payment received.
        """
        if request.query_params.get('payment_id', None):
            return Response(get_customer_payment(
                request.query_params.get('payment_id'),
                params=request.query_params.dict()))
        return Response(list_customer_payments(params=request.query_params.dict()))

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

class BillView(APIView):
    """
    View class for Zoho books bills.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get/List bills.
        """
        if request.query_params.get('bill_id', None):
            response = get_bill(
                request.query_params.get('bill_id'),
                params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        response = list_bills(params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)
    
class SalesOrderView(APIView):
    """
    View class for Zoho books sales order.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get/List sales orders.
        """
        if request.query_params.get('so_id', None):
            response = get_salesorder(
                request.query_params.get('so_id'),
                params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        response = list_salesorders(params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)

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
        total_unpaid_bills = get_unpaid_bills(vendor)
        total_credits = get_available_credit(vendor)
        total_unpaid_invoices = get_unpaid_invoices(vendor)
        return Response({
            "Available_Credits": total_credits,
            "Overdue_Bills": total_unpaid_bills,
            "Outstanding_Invoices": total_unpaid_invoices
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
        return Response({'error': 'Conact name not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """
        add contact addresses.
        """
        if request.data.get('contact_name', None):
            contact_name = request.data.get('contact_name', None)
            return Response(add_contact_address(contact_name, request.data))
        return Response({'error': 'Conact name not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """
        edit contact addresses.
        """
        if request.data.get('contact_name', None) and request.data.get('address_id', None):
            contact_name = request.data.get('contact_name', None)
            address_id = request.data.get('address_id', None)
            return Response(edit_contact_address(contact_name, address_id, request.data))
        return Response({'error': 'Conact name not specified'}, status=status.HTTP_400_BAD_REQUEST)


class ContactPersonView(APIView):
    """
    View class for Zoho books contacts persons.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contact persons.
        """
        contact_id = request.query_params.get('contact_id', None)
        contact_persons_id = request.query_params.get('contact_persons_id', None)
        if contact_id:
            return Response(get_contact_person(contact_id, contact_persons_id, request.query_params))
        response = list_contact_persons(request.query_params)
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        add contact persons.
        """
        contact_id = request.data.get('contact_id', None)
        if contact_id:
            return Response(create_contact_person(request.data))
        return Response({'error': 'Conact id not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """
        edit contact persons.
        """
        if request.data.get('contact_person_id', None):
            contact_person_id = request.data.get('contact_person_id', None)
            return Response(update_contact_person(contact_person_id, request.data))
        return Response({'error': 'Conact person id not specified'}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({"client_code":account_data.get('client_code')})
        return Response({'error': 'Something went wrong!'}, status=status.HTTP_400_BAD_REQUEST)

class VendorClientCodeView(APIView):
    """
    Vendors's client code view
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get vendor client code.
        """
        if request.query_params.get('vendor_name'):
            vendor_name = request.query_params.get('vendor_name')
            try:
                result = search_query('Vendors', vendor_name, 'Vendor_Name')
            except Exception:
                Response({'error': 'Something went wrong!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if result.get('status_code') == 200:
                    data_ls = result.get('response')
                    if data_ls and isinstance(data_ls, list):
                        for vendor in data_ls:
                            if vendor.get('Vendor_Name') == vendor_name:
                                client_code = vendor.get('Client_Code')
                                return Response({"client_code": client_code})
                    return Response({'error': 'Vendor not found in Zoho CRM!'}, status=status.HTTP_400_BAD_REQUEST)
                elif result.get('status_code') == 204:
                    return Response({'error': 'Vendor not found in Zoho CRM!'}, status=status.HTTP_400_BAD_REQUEST)

        if request.query_params.get('legal_business_name'):
            vendor_data = get_vendors_from_crm(request.query_params.get('legal_business_name'))
            return Response({"client_code":vendor_data.get('Client_Code')})
        return Response({'error': 'Something went wrong!'}, status=status.HTTP_400_BAD_REQUEST)

class GetDocumentStatus(APIView):
    """
    View class to get Zoho sign document status.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """
        Get Zoho sign document status.
        """
        request_id = request.query_params.get('request_id')
        if request_id:
            response = get_document(request_id)
            if response['code'] == 0:
                return Response({'code': 0, 'status': response['requests']['request_status']})
            else:
                return Response({'code': 1, 'error': 'Incorrect request id or Document not in Zoho sign'},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response({'code': 1, 'error': 'No request id provided.'}, status=status.HTTP_400_BAD_REQUEST)

class GetSignURL(APIView):
    """
    View class to get Zoho sign url.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """
        Get Zoho sign url.
        """
        request_id = request.query_params.get('request_id')
        action_id = request.query_params.get('action_id')
        if request_id and action_id:
            response = get_embedded_url_from_sign(request_id, action_id)
            if response and response['code'] == 0:
                return Response(response)
            else:
                return Response({'code': 1, 'error': 'Incorrect request id or action id'})
        return Response({'code': 1, 'error': 'No request id or action id provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
class GetDistanceView(APIView):
    """
    View class to get distance between two locations.
    """
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        """
        Get distance.
        """
        account_name = request.data.get('account_name')
        is_ship_changed = request.data.get('is_ship_changed')
        mileage = None
        if not is_ship_changed:
            response = search_query('Accounts', account_name, 'Account_Name')
            if response.get('status_code') == 200:
                for resp in response.get('response'):
                    if resp.get('Round_Trip_Mileage_from_Todd_Rd'):
                        mileage = resp.get('Round_Trip_Mileage_from_Todd_Rd')
                        break
        if not mileage or is_ship_changed:
            location_a = request.data.get('location_a')
            location_b = request.data.get('location_b')
            if location_a and location_b:
                response = get_distance(location_a, location_b)
                if response.get('code'):
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                mileage = float(response.get('distance').get('text').strip(' km'))
        fees = get_transportation_fees()
        if fees.get('response'):
            res = dict()
            data = fees['response'][0]
            res['transportation'] = data
            res['mileage'] = mileage
            return Response(res)
        return Response(
            {'code': 1, 'error': fees},
            status=status.HTTP_400_BAD_REQUEST)

class GetSalesPersonView(APIView):
    """
    View class to get sales person information.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """
        Get sales person.
        """
        account_id = request.query_params.get('account_id')
        response = get_record('Accounts', account_id, full=True)
        if response['status_code'] == 200:
            return Response(response.get('response').get('Owner'))
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class GetNewsFeedView(APIView):
    """
    View class for news feed.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """
        Get news feed.
        """
        type_ = request.query_params.get('type')
        scrapper = Scrapper()
        return Response(scrapper.get_news(type_))

class LabTestView(APIView):
    """
    Delete LabTest.
    """
    authentication_classes = (TokenAuthentication, )

    def delete(self, request, *args, **kwargs):
        """
        Delete LabTest.
        """
        labtest_id = kwargs.get('labtest_id', None)
        if labtest_id:
            try:
                LabTest.objects.get(labtest_crm_id=labtest_id).delete()
                return Response(
                    {'status': 'success'},
                    status=status.HTTP_200_OK
                )
            except LabTest.DoesNotExist:
                pass
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
    
class GetAutoComplete(APIView):
    """
    Autocomplete address using google api.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Get autocomplete address.
        """
        address = request.query_params.get('address')
        if address:
            response = get_places(address)
            if isinstance(response, dict) and response.get('code') == 1:
               Response(response, status=status.HTTP_400_BAD_REQUEST) 
            return Response(response)
        return Response({'code':1, 'error': 'address missing.'}, status=status.HTTP_400_BAD_REQUEST)


class OrderVariableView(viewsets.ReadOnlyModelViewSet):

    """
    Get Order Variables information.
    """
    permission_classes = (IsAuthenticated,)
    queryset = OrderVariable.objects.all()
    serializer_class = OrderVariableSerializer
    filter_backends = [filters.OrderingFilter,DjangoFilterBackend]
    filterset_fields = ['program_type', 'tier']
    

class NotificationView(APIView):
    """
    View class for posting to slack via webhook.
    """
    permission_classes = (IsAuthenticated,)    
    
    def post(self, request):
        """
        add slack notificatiion.
        """
        if request.data.get('channel', None) and request.data.get('message', None):
            try:
                return Response(slack.chat.post_message(request.data.get('channel'), "<!channel> %s" %request.data.get('message'), as_user=True),status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "status_code": 400,
                    "error": e}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Please specify channel/message correctly!'}, status=status.HTTP_400_BAD_REQUEST)
    
