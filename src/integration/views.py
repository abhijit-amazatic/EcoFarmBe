"""
Integration views
"""
from argparse import Action
import time
from datetime import (datetime, timedelta)
import base64
import ast
from io import (BytesIO, )
from django.http import (QueryDict,)
from django.core.exceptions import (ObjectDoesNotExist,)
from django.utils.functional import (cached_property)
from rest_framework import (status,)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, GenericViewSet
from rest_framework import (permissions, viewsets, filters, mixins)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView
from rest_framework.authentication import (TokenAuthentication,)
from django.conf import settings

from core.permissions import UserPermissions
from .models import (Integration, ConfiaCallback, BoxSign, BoxSignDocType)
from inventory.models import Inventory
from integration.box import(
    get_box_tokens, get_shared_link,
    get_client_folder_id, create_folder, get_download_url,
    list_sign_request, create_sign_request, get_sign_request,
    BoxException, BoxAPIException,
    )
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
    get_books_obj,
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
    get_unpaid_invoices, update_available_for_sale,
    get_sub_statuses, approve_estimate, mark_salesorder,
    approve_salesorder, mark_purchaseorder, 
    approve_purchaseorder, mark_invoice, 
    approve_invoice, mark_bill, approve_bill,
    create_sales_order, create_invoice, parse_book_object,
    create_purchase_order, update_sales_order, update_invoice,
)
from integration.sign import (upload_pdf_box, get_document,
                              get_embedded_url_from_sign,
                              download_pdf,
                              send_template)
from integration.task_helpers import (get_box_sign_request_info, box_sign_update_to_db)
from integration.tasks import (send_estimate, delete_estimate_task, upload_agreement_pdf_to_box,)
from integration.utils import (get_distance, get_places)
from core.settings import (INVENTORY_BOX_ID, BOX_CLIENT_ID,
                           BOX_CLIENT_SECRET, CAMPAIGN_HTML_BUCKET, BOOKS_ORGANIZATION_LIST,
                           CONFIA_BASIC_CALLBACK_USER_PW
    )
from slacker import Slacker
from core.mailer import (mail, mail_send,)
from integration.apps.scrapper import (Scrapper, )
from labtest.models import (LabTest,)
from .views_permissions import (
    EstimateViewPermission,
    PurchaseOrderViewPermission,
    VendorPaymentViewPermission,
    CustomerPaymentViewPermission,
    InvoiceViewPermission,
    BillViewPermission,
    SalesOrderViewPermission,
)
from .serializers import (
    BoxSignSerializer,
)
from brand.models import (License, Sign, LicenseProfile)
from bill.models import (Estimate, LineItem)
from integration.campaign import (create_campaign, )
from fee_variable.models import (CampaignVariable, )
from integration.apps.aws import (get_boto_client, create_presigned_url)
from bill.utils import (save_estimate, )
from twilio.twiml.messaging_response import MessagingResponse

if not isinstance(BOOKS_ORGANIZATION_LIST, tuple):
    BOOKS_ORGANIZATION_LIST = BOOKS_ORGANIZATION_LIST.split(',')
    
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
        record_id = request.query_params.get('id', None)
        legal_business_name = request.query_params.get('legal_business_name', None)
        name = request.query_params.get('name', None)
        if module and record_id:
            record = get_record(module, record_id)
            if record['status_code'] == 200:
                return Response(record, status=status.HTTP_200_OK)
            return Response(record, status=status.HTTP_400_BAD_REQUEST)
        elif module and legal_business_name:
            record = search_query(module, legal_business_name, 'Account_Business_DBA')
            if record['status_code'] == 200:
                return Response(record, status=status.HTTP_200_OK)
            return Response(record, status=status.HTTP_400_BAD_REQUEST)
        elif module and name:
            field_dict = {
                'Accounts': 'Account_Name',
                'Vendors': 'Vendor_Name',
                'Contacts': ('First_Name', 'Last_Name')
            }
            if module == 'Contacts':
                for field in field_dict.get(module):
                    response_1 = search_query(module, name, field, case_insensitive=True)
                    response_2 = search_query(module, name, field, case_insensitive=True)
                    if response_1['status_code'] == 200 and response_2['status_code'] == 200:
                        response_1['response'].append(response_2['response'])
                        return Response(response_1)
            response = search_query(module, name, field_dict.get(module), case_insensitive=True)
            if response['status_code'] == 200:
                return Response(response, status=status.HTTP_200_OK)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
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
        elif request.query_params.get('module') == 'Orgs':
            return Response(get_picklist('Orgs', request.query_params['field']))
        elif request.query_params.get('module') == 'Licenses':
            return Response(get_picklist('Licenses', request.query_params['field']))
        elif request.query_params.get('module') == 'Leads':
            return Response(get_picklist('Leads', request.query_params['field']))
        return Response(get_picklist('Vendors', request.query_params['field']))

    def get_permissions(self):
        if self.request.query_params['field'] in ('Region', 'County'):
            self.permission_classes = [AllowAny, ]
        else:
            self.permission_classes = [IsAuthenticated, ]
        return super(GetPickListView, self).get_permissions()

class GetLeadsCompanyTypeListView(APIView):
    """
    Get Leads Company Type choices from Zoho CRM.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Get picklist.
        """
        return Response(get_picklist('Leads', 'Company_Type'))


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
        if self.request.query_params['field'] in ('Products of Interest',):
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


class LicenseBillingAndAccountingAPI(APIView):
    permission_classes = (IsAuthenticated,)

    CRM_PROFILES_MAP = {
        'customer': 'account',
        'vendor': 'vendor',
    }

    contact_type = 'vendor'
    detail_view_key = 'id'
    func = {
        'get_func': None,
        'list_func': None,
    }

    def get(self, request):
        """
        Get PO.
        """
        get_func = self.func.get('get_func')

        params = request.query_params.dict()
        organization_name = params.get('organization_name')
        if params.get(self.detail_view_key, None):
            return Response(get_func(
                organization_name,
                params.get(self.detail_view_key),
                params=params))
        else:
            if organization_name == 'all':
                result = dict()
                for books_name in BOOKS_ORGANIZATION_LIST:
                    result[books_name] = self.list_func(books_name, params=params)
                return Response(result)
            else:
                response = self.list_func(organization_name, params=params)
                if response.get('code') and response['code'] != 0:
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
                return Response(response, status=status.HTTP_200_OK)

    def list_func(self, books_name, params):
        list_func = self.func.get('list_func')
        if 'license_id' in self.request.query_params:
            params[f'{self.contact_type}_id'] = self.get_contact_id(books_name) or '0'
        return list_func(books_name, params=params)

    @cached_property
    def license_obj(self):
        license_id = self.request.query_params.get('license_id', '')
        try:
            license_obj = License.objects.prefetch_related('license_profile').get(id=license_id)
        except ObjectDoesNotExist:
            raise ValidationError({'license_id': f'License id {license_id} does not exist.'})

        except ValueError:
            raise ValidationError({'license_id': f'Invalid value passed \'{license_id}\' to license_id.'})
        else:
            return license_obj

    def get_contact_id(self, organization_name=None):
        params = self.request.query_params.dict()
        books_name = organization_name or params.get('organization_name') or ''
        org_name = books_name.replace('books_', '')
        contact_id = None
        if 'license_id' in params:
            contact_ids = getattr(self.license_obj, f'zoho_books_{self.contact_type}_ids')
            if contact_ids.get(org_name):
                contact_id = contact_ids.get(org_name).strip()
            if not contact_id:
                try:
                    lp = License.license_profile
                except ObjectDoesNotExist:
                    pass
                else:
                    crm_profile_id = getattr(lp, f'zoho_crm_{self.CRM_PROFILES_MAP.get(self.contact_type)}_id')
                    if not crm_profile_id:
                        if self.contact_type == 'customer':
                            r = search_query('Accounts', self.license_obj.client_id, 'Client_ID')
                        else:
                            r = search_query('Vendors', self.license_obj.client_id, 'Client_ID')
                        if r['status_code'] == 200:
                            for crm_profile in r['response']:
                                if crm_profile['Client_ID'] == self.license_obj.client_id:
                                    crm_profile_id = crm_profile['id']
                                    break

                    books_obj = get_books_obj(f'books_{org_name}')
                    contact_obj = books_obj.Contacts()
                    r = contact_obj.get_contact_using_crm_account_id(crm_profile_id)
                    try:
                        if r and r.get('code') == 0:
                            for c in r.get('contacts', []):
                                if c.get('contact_type') == self.contact_type:
                                    if c.get('contact_id'):
                                        contact_id = c.get('contact_id')
                    except Exception as e:
                        print(e)

            if not contact_id:
                raise ValidationError(
                    {
                        "code": 1004,
                        "message": (
                            f'Unable to find {org_name.upper()} {self.contact_type} id '
                            f'for license id \'{params.get("license_id")}\'.',
                        )
                    }
                )

        return contact_id


class EstimateView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books estimates.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'customer'
    detail_view_key = 'estimate_id'
    func = {
        'get_func': get_estimate,
        'list_func': list_estimates,
    }

    def post(self, request):
        """
        Create and estimate in Zoho Books. 
        """
        params = request.query_params.dict()
        organization_name = params.get('organization_name')
        if 'license_id' in self.request.query_params:
            request.data[f'{self.contact_type}_id'] = self.get_contact_id(organization_name)
        response = create_estimate(organization_name, data=request.data, params=params)
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        # estimate_obj = save_estimate(request)
        customer_name = request.data.get('customer_name')
        delete_estimate_task.delay(customer_name)
        return Response(response)

    def put(self, request):
        """
        Update an estimate in Zoho Books.
        """
        organization_name = request.query_params.get('organization_name')
        if 'license_id' in self.request.query_params:
            request.data[f'{self.contact_type}_id'] = self.get_contact_id(organization_name)
        is_draft = request.query_params.get('is_draft')
        delete_estimate_from_db = request.query_params.get('delete_estimate_from_db', False)
        estimate_id = request.data['estimate_id']
        if is_draft == 'true' or is_draft == 'True':
            response = update_estimate(organization_name, estimate_id=estimate_id, \
                data=request.data, params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            # estimate_obj = save_estimate(request)
            if delete_estimate_from_db:
                customer_name = response.get('customer_name')
                delete_estimate_task.delay(customer_name)
            return Response(response)
        else:
            estimate = update_estimate(organization_name, estimate_id=estimate_id, \
                data=request.data, params=request.query_params.dict())
            if estimate.get('code') and estimate['code'] != 0:
                return Response(estimate, status=status.HTTP_400_BAD_REQUEST)
            # update_available_for_sale(request.data)
            customer_name = estimate.get('customer_name')
            delete_estimate_task.delay(customer_name)
            return Response(estimate)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Delete an estimate from Zoho books.
        """
        organization_name = request.query_params.get('organization_name')
        estimate_id = request.data.get('estimate_id')
        customer_name = request.data.get('customer_name')
        if estimate_id:
            return Response(delete_estimate(organization_name, estimate_id=estimate_id, params=request.query_params.dict()))
        if customer_name:
            delete_estimate_task.delay(customer_name)
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
        organization_name = request.query_params.get('organization_name')
        if estimate_id and address_type:
            response = update_estimate_address(organization_name, estimate_id, address_type, request.data)
            if response.get('code') and response.get('code') != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class EstimateSignView(LicenseBillingAndAccountingAPI):
    """
    View class to sign for estimate.
    """
    permission_classes = (IsAuthenticated,)
    contact_type = 'customer'
    detail_view_key = 'estimate_id'

    def get(self, request):
        """
        Get signing url.
        """
        estimate_id = request.query_params.get('estimate_id', None)
        customer_name = request.query_params.get('customer_name', None)
        organization_name = request.query_params.get('organization_name')
        customer_id = None
        if 'license_id' in self.request.query_params:
            customer_id = self.get_contact_id(organization_name)
        if estimate_id and customer_id:
            response = send_estimate_to_sign(organization_name, estimate_id, customer_id, customer_name)
            if response.get('code') and response.get('code') != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class TemplateSignView(APIView):
    """
    View class to sign for template.
    """
    permission_classes = (IsAuthenticated,)

    def compare_fields(self, fields):
        """
        Compare fields with request.data fields.
        """
        for field, value in fields.items():
            if self.request.data.get(field) != value:
                return True
        return False

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

        try:
            license = License.objects.get(license_number=licenses[0])
            obj = Sign.objects.get(license=license)
            if obj:
                is_agreement_changed = self.compare_fields(obj.fields)
                if not is_agreement_changed:
                    response = get_embedded_url_from_sign(obj.request_id, obj.action_id)
                    if response['code'] == 0:
                        return Response(response)
        except (License.DoesNotExist, Sign.DoesNotExist) as exc:
            pass

        if template_id and recipient:
            response = send_template(template_id,
                                     recipient,licenses,
                                     legal_business_names,
                                     EIN, SSN, business_structure,
                                     license_owner_name, premise_address,
                                     premise_state, premise_city, premise_zip,
                                     license_owner_email)
            print('Send_template in API view  >>>', response, dir(response))
            try:
                license = License.objects.get(license_number=licenses[0])
                data = {"request_id":response['request_id'],
                        "action_id":response['action_id'],
                        "fields":request.data}
                obj = Sign.objects.update_or_create(license=license,
                                    defaults=data)
            except (License.DoesNotExist, Sign.DoesNotExist):
                pass
            return Response(response)
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
            new_folder = create_folder(folder_id, 'Agreements')
            offline_folder = create_folder(new_folder, 'Offline')
            for document in data.get('document_ids'):
                filename = document.get('document_name')
                file_id = upload_pdf_box(request_id, offline_folder, filename, True)
                response.append(get_download_url(file_id))
                License.objects.filter(legal_business_name=business_dba).update(is_contract_downloaded=True)
        return Response(response)


class BoxSignViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    """
    View class to sign for template.
    """
    queryset = BoxSign.objects.get_queryset().select_related('license')
    permission_classes = (IsAuthenticated,)
    serializer_class = BoxSignSerializer

    lookup_field = 'request_id'

    def get_object(self):
        obj = super().get_object()
        return box_sign_update_to_db(obj)

    def create(self, request, *args, **kwargs):
        """
        Create agreement sign request.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # try:
        #     doc_type_obj = BoxSignDocType.objects.get(name=validated_data['doc_type'])
        # except ObjectDoesNotExist:
        #     return Response({"detail": f"Doc type '{validated_data['doc_type']}' not configured on backend."}, status=400)

        try:
            obj = BoxSign.objects.filter(license=validated_data['license']).latest('created_on')
            if obj:
                # if all([validated_data.get(k) == v for k, v in obj.fields.items()]):
                if self.is_fields_same(obj.fields, serializer.initial_data):
                    if obj.status not in ('cancelled', 'declined', 'error_converting', 'error_sending', 'expired'):
                        if obj.signer_decision not in ('declined',):
                            obj = box_sign_update_to_db(obj)
                            serializer = self.get_serializer(obj)
                            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as exc:
            pass


        signer_order = 1
        signers = [
            {
                'name': validated_data['recipient']['name'],
                'email': validated_data['recipient']['email'],
                'embed_url_external_user_id': self.request.user.email,
                'is_in_person': True,
                'order': signer_order,
            },
        ]

        if validated_data['doc_type'].need_approval:
            try:
                doc_type_approver = validated_data['doc_type'].approver
            except ObjectDoesNotExist:
                return Response({'Agreement doc_type Approver details not added.'}, status=400)
            else:
                validated_data['prefill_tags'].update(doc_type_approver.get_prefill_data())
                signer_order += 1
                signers.append({
                    'name': doc_type_approver.name,
                    'email': doc_type_approver.email,
                    'is_in_person': False,
                    'order': signer_order,
                })

        for reader in validated_data['doc_type'].final_copy_readers.all():
            signer_order += 1
            signers.append({
                'name': reader.name,
                'email': reader.email,
                'role': 'final_copy_reader',
                'is_in_person': False,
                'order': signer_order,
            })
        try:
            license_folder = create_folder(
                settings.LICENSE_PARENT_FOLDER_ID,
                f"{validated_data['license'].legal_business_name}_{validated_data['license'].license_number}",
            )
            parent_folder = create_folder(license_folder,validated_data['doc_type'].name.title())

            response = create_sign_request(
                source_file_id=validated_data.get('source_file_id'),
                parent_folder_id=parent_folder,
                signers=signers,
                prefill_tags=validated_data['prefill_tags'],
                external_id=validated_data['license'].license_number
            )
        except BoxAPIException as e:
            response = e.network_response.json()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            defaults = {
                **get_box_sign_request_info(response),
                "doc_type": validated_data['doc_type'],
                "program_name": validated_data.get('program_name'),
                "status": response['status'],
                "license": validated_data['license'],
                "fields": serializer.initial_data,
                "response": response,
            }
            obj, created = BoxSign.objects.update_or_create(request_id=response['id'], defaults=defaults)
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)

    # def retrieve(self, request, *args, **kwargs):
    #     request_id = kwargs.get('pk')
    #     response = get_sign_request(request_id, params=request.query_params.dict())
    #     return Response(response)

    # def destroy(self, request, *args, **kwargs):
    #     pass

    @action(detail=True, url_path='download', methods=['get'])
    def download(self, request,*args, **kwargs):
        """
        Get document binary.
        """
        response = list()
        obj = super().get_object()
        response.append(get_download_url(obj.output_file_id))
        if not obj.license.is_contract_downloaded:
            obj.license.is_contract_downloaded = True
            obj.license.save()
        return Response(response)

    def is_fields_same(self, dict1, dict2):
        """
        Check fields are same or not.
        """
        if len(dict1) != len(dict2):
            return False
        for k, v in dict1.items():
            if isinstance(v, dict):
                if not self.is_fields_same(dict2.get(k), v):
                    return False
            else:
                if dict2.get(k) != v:
                    return False
        return True



class EstimateTaxView(APIView):
    """
    View class to calculate tax for estimate.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get estimates tax.
        """
        organization_name = request.query_params.get('organization_name')
        product_category = request.query_params.get('product_category', None)
        quantity = request.query_params.get('quantity', None)
        if product_category and quantity:
            return Response(calculate_tax(organization_name, product_category, quantity))
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
        organization_name = request.query_params.get('organization_name')
        if estimate_id and status:
            return Response(mark_estimate(organization_name, estimate_id, status))
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
        organization_name = request.query_params.get('organization_name')
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
                new_folder = create_folder(folder_id, 'Agreements')
                upload_agreement_pdf_to_box.delay(request_id, new_folder, filename, document_number)
            else:
                a = mark_estimate(organization_name, estimate_id, 'sent')
                a = mark_estimate(organization_name, estimate_id, 'accepted')
                new_folder = create_folder(folder_id, 'Estimates')
                try:
                    estimate_obj = Estimate.objects.get(estimate_id=estimate_id)
                    estimate_obj.db_status = 'signed'
                    estimate_obj.save()
                except Estimate.DoesNotExist:
                    pass
                upload_pdf_box.delay(request_id, new_folder, filename, is_agreement)
        if order_number:
            try:
                order_data = get_estimate(estimate_id,params={})
                if order_data.get('estimate_id'):
                    item_total = '{:,.2f}'.format(sum(i['item_total'] for i in order_data.get('line_items',[])))
                    quantity = sum(i['quantity'] for i in order_data.get('line_items',[]))
                    prod_category = Inventory.objects.filter(item_id__in=[i['item_id'] for i in  order_data.get('line_items')],parent_category_name__isnull=False).values_list('parent_category_name',flat=True).distinct()
                    category = ",".join(list(prod_category))
                    mail("order.html",{'link': settings.FRONTEND_DOMAIN_NAME+'dashboard/billing/estimates/%s/item' % estimate_id,'full_name': request.user.full_name,'order_number':order_number,'business_name': business_dba, 'license_number': document_number, 'estimate_id':estimate_id, 'order_amount':item_total,'quantity':quantity,'product_category':category},"Your Thrive Society Order %s." %order_number, request.user.email,file_data=download_pdf(request_id))
            except Exception as e:
                print('Issue while preparing order email', e)
        return Response({'message': 'Success'})

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


class PurchaseOrderView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books purchase orders.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'vendor'
    detail_view_key = 'po_id'
    func = {
        'get_func': get_purchase_order,
        'list_func': list_purchase_orders,
    }

class VendorPaymentView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books vendor payments.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'vendor'
    detail_view_key = 'payment_id'
    func = {
        'get_func': get_vendor_payment,
        'list_func': list_vendor_payments,
    }

class CustomerPaymentView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books customer payments received.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'customer'
    detail_view_key = 'payment_id'
    func = {
        'get_func': get_customer_payment,
        'list_func': list_customer_payments,
    }

class InvoiceView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books invoices.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'customer'
    detail_view_key = 'invoice_id'
    func = {
        'get_func': get_invoice,
        'list_func': list_invoices,
    }

    def put(self, request):
        """
        Update invoice.
        """
        params = request.query_params.dict()
        organization_name = params.get('organization_name')
        invoice_id = request.data['invoice_id']
        response = update_invoice(organization_name, invoice_id=invoice_id, data=request.data, params=params)
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)

class BillView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books bills.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'vendor'
    detail_view_key = 'bill_id'
    func = {
        'get_func': get_bill,
        'list_func': list_bills,
    }

class SalesOrderView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books sales order.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'customer'
    detail_view_key = 'so_id'
    func = {
        'get_func': get_salesorder,
        'list_func': list_salesorders,
    }

    def put(self, request):
        """
        Update sales order.
        """
        organization_name = request.query_params.get('organization_name')
        salesorder_id = request.data['salesorder_id']
        response = update_sales_order(organization_name, salesorder_id=salesorder_id, data=request.data, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)

class SalesOrderSubStatusesView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books sales order sub statuses.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get/List sales orders sub statuses.
        """
        organization_name = request.query_params.get('organization_name')
        response = get_sub_statuses(organization_name, params=request.query_params.dict())
        return Response(response, status=status.HTTP_200_OK)

class VendorCreditView(LicenseBillingAndAccountingAPI):
    """
    View class for Zoho books vendor credit.
    """
    permission_classes = (IsAuthenticated,)

    contact_type = 'vendor'
    detail_view_key = 'credit_id'
    func = {
        'get_func': get_vendor_credit,
        'list_func': list_vendor_credits,
    }

class AccountSummaryView(APIView):
    """
    View class for Zoho books summary.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get account summary.
        """
        organization_name = request.query_params.get('organization_name')
        vendor = request.query_params.get('vendor_name')
        try:
            if organization_name == 'all':
                org_result = dict()
                for org in BOOKS_ORGANIZATION_LIST:
                    org_result[org] = {"Available_Credits":get_available_credit(org,vendor),
                                       "Overdue_Bills": get_unpaid_bills(org,vendor),
                                       "Outstanding_Invoices": get_unpaid_invoices(org,vendor)}
                    time.sleep(0.5)
                if org_result:
                    return Response({
                        "Available_Credits": sum([i['Available_Credits'] for i in org_result.values()]),
                        "Overdue_Bills": sum([i['Overdue_Bills'] for i in org_result.values()]),
                        "Outstanding_Invoices": sum([i['Outstanding_Invoices'] for i in org_result.values()])
                    })
            total_unpaid_bills = get_unpaid_bills(organization_name, vendor)
            total_credits = get_available_credit(organization_name, vendor)
            total_unpaid_invoices = get_unpaid_invoices(organization_name, vendor)    
            return Response({
                "Available_Credits": total_credits,
                "Overdue_Bills": total_unpaid_bills,
                "Outstanding_Invoices": total_unpaid_invoices
            })
        except Exception as e:
            return Response({"status":"Something went wrong!Pleae check vendor/legal business names.","error": e})
        
class ContactView(APIView):
    """
    View class for Zoho books contacts.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contact.
        """
        organization_name = request.query_params.get('organization_name')
        if request.query_params.get('contact_id', None):
            return Response(get_contact(organization_name, request.query_params.get('contact_id')))
        return Response(list_contacts(organization_name, params=request.query_params.dict()))

    def post(self, request):
        """
        Create contact in Zoho Books.
        """
        organization_name = request.query_params.get('organization_name')
        return Response(create_contact(organization_name, data=request.data, params=request.query_params.dict()))

class ContactAddressView(APIView):
    """
    View class for Zoho books contacts address.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get contact addresses.
        """
        organization_name = request.query_params.get('organization_name')
        if request.query_params.get('contact_id', None):
            return Response(get_contact_addresses(organization_name, request.query_params.get('contact_id')))
        return Response({'error': 'Conact name not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """
        add contact addresses.
        """
        organization_name = request.query_params.get('organization_name')
        if request.data.get('contact_id', None):
            contact_id = request.data.get('contact_id', None)
            return Response(add_contact_address(organization_name, contact_id, request.data))
        return Response({'error': 'Conact name not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """
        edit contact addresses.
        """
        organization_name = request.query_params.get('organization_name')
        if request.data.get('contact_id', None) and request.data.get('address_id', None):
            contact_id = request.data.get('contact_id', None)
            address_id = request.data.get('address_id', None)
            return Response(edit_contact_address(organization_name, contact_id, address_id, request.data))
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
        organization_name = request.query_params.get('organization_name')
        if contact_id:
            return Response(get_contact_person(organization_name, contact_id, contact_persons_id, request.query_params))
        response = list_contact_persons(organization_name, request.query_params)
        return Response(response, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        add contact persons.
        """
        contact_id = request.data.get('contact_id', None)
        organization_name = request.query_params.get('organization_name')
        if contact_id:
            return Response(create_contact_person(organization_name, request.data))
        return Response({'error': 'Conact id not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """
        edit contact persons.
        """
        organization_name = request.query_params.get('organization_name')
        if request.data.get('contact_person_id', None):
            contact_person_id = request.data.get('contact_person_id', None)
            return Response(update_contact_person(organization_name, contact_person_id, request.data))
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
        organization_name = request.query_params.get('organization_name')
        return Response(get_tax_rates(organization_name))
        
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
            client_code = ''
            try:
                result = search_query('Vendors', vendor_name, 'Vendor_Name')
            except Exception:
                result = {}
            else:
                if result.get('status_code') == 200:
                    data_ls = result.get('response')
                    if data_ls and isinstance(data_ls, list):
                        for vendor in data_ls:
                            if vendor.get('Vendor_Name') == vendor_name:
                                client_code = vendor.get('Client_Code')
                                if client_code:
                                    return Response({"client_code": client_code})

            if result.get('status_code') == 204 or not client_code:
                try:
                    result = search_query('Accounts', vendor_name, 'Account_Name')
                except Exception:
                    Response({'error': 'Something went wrong!'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    if result.get('status_code') == 200:
                        data_ls = result.get('response')
                        if data_ls and isinstance(data_ls, list):
                            for account in data_ls:
                                if account.get('Account_Name') == vendor_name:
                                    client_code = account.get('Client_Code')
                                    return Response({"client_code": client_code})
                        return Response({'error': 'Vendor or Account not found in Zoho CRM!'}, status=status.HTTP_400_BAD_REQUEST)
                    elif result.get('status_code') == 204:
                        return Response({'error': 'Vendor or Account not found in Zoho CRM!'}, status=status.HTTP_400_BAD_REQUEST)

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
        organization_name = request.query_params.get('organization_name')
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
        fees = get_transportation_fees(organization_name)
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
                return Response(slack.chat.post_message(request.data.get('channel'), "<!channel> %s" %request.data.get('message'), as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL),status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "status_code": 400,
                    "error": e}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Please specify channel/message correctly!'}, status=status.HTTP_400_BAD_REQUEST)
    
class CampaignView(APIView):
    """
    View class for Zoho Campaign.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Create zoho campaign.
        """
        campaign_name = request.data.get('campaign_name')
        campaign_subject = request.data.get('campaign_subject')
        content_data = request.data.get('content_data')

        file_name = f'{campaign_subject}.html'
        file_obj = BytesIO(bytes(content_data.encode('utf-8')))

        client = get_boto_client('s3')
        response = client.upload_fileobj(file_obj, CAMPAIGN_HTML_BUCKET, file_name)
        response = create_presigned_url(CAMPAIGN_HTML_BUCKET, file_name)
        if response['status_code'] == 0:
            content_url = response['response']
        else:
            return Response({'error': 'error occured while upload file to s3.'}, status=status.HTTP_400_BAD_REQUEST)

        vars = CampaignVariable.objects.values('from_email', 'mailing_list_id')[0]
        list_details = dict()
        mailing_list_ids = ast.literal_eval(vars['mailing_list_id'][0])
        for mailing_list in mailing_list_ids:
            list_details[mailing_list] = []
        return Response(create_campaign(campaign_name, vars['from_email'], campaign_subject, list_details, content_url))

class MarkEstimateView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        _status = request.data.get('status')
        estimate_id = request.data.get('estimate_id')
        if estimate_id and _status:
            response = mark_estimate(organization_name, estimate_id, _status)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ApproveEstimateView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        estimate_id = request.data.get('estimate_id')
        if estimate_id:
            response = approve_estimate(organization_name, estimate_id)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class MarkSalesOrderView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        _status = request.data.get('status')
        salesorder_id = request.data.get('salesorder_id')
        if salesorder_id and _status:
            response = mark_salesorder(organization_name, salesorder_id, _status)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ApproveSalesOrderView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        salesorder_id = request.data.get('salesorder_id')
        if salesorder_id:
            response = approve_salesorder(organization_name, salesorder_id)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class MarkPurchaseOrderView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        _status = request.data.get('status')
        purchase_id = request.data.get('purchaseorder_id')
        if purchase_id and _status:
            response = mark_purchaseorder(organization_name, purchase_id, _status)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ApprovePurchaseOrderView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        purchaseorder_id = request.data.get('purchaseorder_id')
        if purchaseorder_id:
            response = approve_salesorder(organization_name, purchaseorder_id)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class MarkInvoiceView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        _status = request.data.get('status')
        invoice_id = request.data.get('invoice_id')
        if invoice_id and _status:
            response = mark_invoice(organization_name, invoice_id, _status)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ApproveInvoiceView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        invoice_id = request.data.get('invoice_id')
        if invoice_id:
            approve_invoice(organization_name, invoice_id)
            return Response({'response': 'Success'})
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class MarkBillView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        _status = request.data.get('status')
        bill_id = request.data.get('bill_id')
        if bill_id and _status:
            response = mark_bill(organization_name, bill_id, _status)
            return Response(response)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ApproveBillView(APIView):
    """
    View class for Zoho status.
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        """
        Change status.
        """
        organization_name = request.query_params.get('organization_name')
        bill_id = request.data.get('bill_id')
        if bill_id:
            approve_bill(organization_name, bill_id)
            return Response({'response': 'Success'})
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ConvertEstimateToSalesOrder(APIView):
    """
    View class to convert Estimate to Sales order.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Convert document.
        """
        organization_name = request.query_params.get('organization_name')
        estimate_id = request.data.get('estimate_id')
        if estimate_id:
            estimate = get_estimate(organization_name, estimate_id=estimate_id, params={})
            estimate['custom_fields'] = [f for f in estimate.get('custom_fields', []) if f.get('placeholder') not in ('cf_payment_terms', 'cf_payment_method',)]
            estimate = parse_book_object('sales_order', estimate)
            so = create_sales_order(organization_name, estimate)
            if so.get('code') != 0:
                return Response(so, status=status.HTTP_400_BAD_REQUEST)
            return Response(so)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ConvertSalesOrderToInvoice(APIView):
    """
    View class to convert Sales order to Invoice.
    """
    permission_classes = (IsAuthenticated,)
    cf_filter = (
        # "cf_thrive_society_s_payment_in",
        # "cf_license",
        # "cf_tax_terms",
        # "cf_total_margin",
        "cf_client_code",
        "cf_client_license",
        "cf_billing_published",
    )

    def post(self, request):
        """
        Convert document.
        """
        organization_name = request.query_params.get('organization_name')
        sales_order_id = request.data.get('salesorder_id')
        if sales_order_id:
            so = get_salesorder(organization_name, so_id=sales_order_id, params={})
            so['custom_fields'] = [f for f in so.get('custom_fields', []) if f.get('placeholder') in self.cf_filter]
            so = parse_book_object('salesorder_to_invoice', so, line_item_parser='salesorder_to_invoice_parser')
            so['custom_fields'] += [{"api_name": "cf_tax_terms", "value": ["Applicable "]},]
            invoice = create_invoice(organization_name, so)
            if invoice.get('code') != 0:
                return Response(invoice, status=status.HTTP_400_BAD_REQUEST)
            return Response(invoice)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ConvertEstimateToInvoice(APIView):
    """
    View class to convert estimate to Invoice.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Convert document.
        """
        organization_name = request.query_params.get('organization_name')
        estimate_id = request.data.get('estimate_id')
        if estimate_id:
            estimate = get_estimate(organization_name, estimate_id=estimate_id, params={})
            estimate = parse_book_object('invoice', estimate)
            invoice = create_invoice(organization_name, estimate)
            if invoice.get('code') != 0:
                return Response(invoice, status=status.HTTP_400_BAD_REQUEST)
            return Response(invoice)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class ConvertSalesOrderToPurchaseOrder(APIView):
    """
    View class to convert Sales order to Purchase order.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Convert document.
        """
        organization_name = request.query_params.get('organization_name')
        sales_order_id = request.data.get('salesorder_id')
        if sales_order_id:
            so = get_salesorder(organization_name, so_id=sales_order_id, params={})
            so = parse_book_object('purchase_order', so)
            purchase_order = create_purchase_order(organization_name, so)
            if purchase_order.get('code') != 0:
                return Response(purchase_order, status=status.HTTP_400_BAD_REQUEST)
            return Response(purchase_order)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ChatbotView(APIView):
    """
    Webhook for twilio chatbot.Currenty this is a sample view & can be modified according to logic once that is clear.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Accepts post requests for messages 
        """
        incoming_msg = request.data.get('Body', '').lower()
        resp = MessagingResponse()
        msg = resp.message()
        responded = False
        if 'quote' in incoming_msg:
            # return a quote
            quote = f'This is only For quote testing.'
            msg.body(quote)
            responded = True
        if 'image' in incoming_msg:
            # return a test product image 
            msg.media('https://dev.ecofarm.app/static/media/new_logo.4ae646fa.png')
            responded = True
        if not responded:
            msg.body('I only know about related quotes and product images, sorry!')
        return Response({str(resp)})

    

class ConfiaCallbackView(APIView):
    """
    View class to add confia callbacks
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        save/update confia callback data.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token_type, _, credentials = auth_header.partition(' ')
        expected = base64.b64encode(CONFIA_BASIC_CALLBACK_USER_PW.encode()).decode()
        if token_type != 'Basic' or credentials != expected:
            return  Response({'Error':"Auth Creds are not valid/provided"}, status=status.HTTP_400_BAD_REQUEST)
        default_data = {
            "partner_company_id":request.data.get('partnerCompanyId'),
            "confia_member_id":request.data.get('memberId'),
            "status": request.data.get('status')
        }
        obj,created =  ConfiaCallback.objects.update_or_create(partner_company_id=request.data.get('partnerCompanyId'),defaults=default_data)
        if obj:
            try:
                lic_obj = LicenseProfile.objects.get(license__client_id=int(obj.partner_company_id))
                lic_obj.is_confia_member = True
                lic_obj.save()
            except Exception as e:
                print("Error while updating is_confia_member flag from LicenseProfile", e)
            return Response({'Success': "Member onboarded/status updated!"},status=status.HTTP_200_OK)
        
    
