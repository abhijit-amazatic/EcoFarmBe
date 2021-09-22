"""
Views for Inventory
"""
import operator
import time
from datetime import datetime, timedelta
from io import BytesIO, BufferedReader
from mimetypes import MimeTypes
from functools import reduce
import django_filters
from django.shortcuts import (render, )
from django.db.models import (Sum, F, Min, Max, Avg, Q, Func, ExpressionWrapper, DateField,)
from django.utils import  timezone
from rest_framework.views import APIView
from rest_framework.viewsets import (GenericViewSet, mixins)
from rest_framework.response import (Response, )
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework import (viewsets, status,)
from rest_framework.filters import (OrderingFilter, )
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from django.core.paginator import Paginator
from core.pagination import PageNumberPagination
from .serializers import (
    InventorySerializer,
    LogoutInventorySerializer,
    ItemFeedbackSerializer,
    InTransitOrderSerializer,
    CustomInventorySerializer,
    InventoryItemEditSerializer,
    InventoryItemQuantityAdditionSerializer,
    InventoryItemDelistSerializer,
)
from .models import (
    Inventory,
    ItemFeedback,
    InTransitOrder,
    Documents,
    CustomInventory,
    InventoryItemEdit,
    InventoryItemQuantityAddition,
    InventoryItemDelist,
)
from core.settings import (AWS_BUCKET,)
from integration.apps.aws import (create_presigned_url, create_presigned_post,)
from .permissions import (DocumentPermission, InventoryPermission, )
from integration.box import (delete_file, get_file_obj,)
from brand.models import (License, Brand, LicenseProfile, Organization, )
from user.models import (User, )
from labtest.models import (LabTest, )
from cultivar.models import (Cultivar, )
from integration.inventory import (
    sync_inventory, upload_inventory_document,
    get_inventory_name, update_inventory_item, get_contacts,
    get_inventory_summary, get_category_count,
    get_packages, get_sales_returns, get_inventory_metadata,
    update_package, update_sales_return, update_contact, create_package,
    get_books_name_from_inventory_name, get_books_name_from_inventory_name)
from .tasks import (
    notify_inventory_item_submitted_task,
    create_duplicate_crm_vendor_from_crm_account_task,
    get_custom_inventory_data_from_crm_task,
    inventory_item_quantity_addition_task,
    notify_inventory_item_change_submitted_task,
    notify_inventory_item_delist_submitted_task,
    async_update_inventory_item,
)
from integration.books import (get_salesorder, parse_book_object)
from .utils import delete_in_transit_item
from bill.tasks import remove_estimates_after_intransit_clears
from bill.models import (Estimate, LineItem, )
from bill.utils import (parse_fields, get_notify_addresses, save_estimate, save_estimate_from_intransit, parse_intransit_to_pending,)


class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):   
    name__in = CharInFilter(field_name='name', lookup_expr='in')
    product_type__in = CharInFilter(field_name='product_type', lookup_expr='in')
    cf_cultivar_type__in = CharInFilter(field_name='cf_cultivar_type', lookup_expr='in')
    category_name = CharInFilter(method='category_name__in', lookup_expr='in')
    vendor_name__in = CharInFilter(field_name='vendor_name', lookup_expr='in')
    cf_vendor_name__in = CharInFilter(field_name='cf_vendor_name', lookup_expr='in')
    cf_strain_name = CharInFilter(method='cf_strain_name__in', lookup_expr='in')
    cf_client_code = CharInFilter(method='cf_client_code__in', lookup_expr='in')
    cf_cultivation_type = CharInFilter(method='cf_cultivation_type__in', lookup_expr='in')
    cf_cannabis_grade_and_category__in = CharInFilter(field_name='cf_cannabis_grade_and_category', lookup_expr='in')
    cf_pesticide_summary__in = CharInFilter(method='filter_cf_pesticide_summary__in', lookup_expr='in')
    cf_testing_type__in = CharInFilter(field_name='cf_testing_type', lookup_expr='in')
    cf_status__in = CharInFilter(field_name='cf_status', lookup_expr='in')
    cf_quantity_estimate__in = CharInFilter(field_name='cf_quantity_estimate', lookup_expr='in')
    cultivar = django_filters.CharFilter(method='get_cultivars')
    tags = django_filters.CharFilter(method='get_tags')
    nutrients = django_filters.CharFilter(method='get_nutrients')
    ethics_and_certification = django_filters.CharFilter(method='get_ethics_and_certification')
    county_grown = django_filters.CharFilter(method='get_county_grown')
    appellation = django_filters.CharFilter(method='get_appellation')
    labtest__CBD__in = CharInFilter(field_name='labtest__CBD', lookup_expr='in')
    labtest__THC__in = CharInFilter(field_name='labtest__THC', lookup_expr='in')
    labtest__d_8_THC__in = CharInFilter(field_name='labtest__d_8_THC', lookup_expr='in')
    labtest__THCA__in = CharInFilter(field_name='labtest__THCA', lookup_expr='in')
    labtest__CBDA__in = CharInFilter(field_name='labtest__CBDA', lookup_expr='in')
    labtest__CBN__in = CharInFilter(field_name='labtest__CBN', lookup_expr='in')
    labtest__CBC__in = CharInFilter(field_name='labtest__CBC', lookup_expr='in')
    labtest__CBCA__in = CharInFilter(field_name='labtest__CBCA', lookup_expr='in')
    labtest__CBGA__in = CharInFilter(field_name='labtest__CBGA', lookup_expr='in')
    labtest__CBG__in = CharInFilter(field_name='labtest__CBG', lookup_expr='in')
    labtest__CBL__in = CharInFilter(field_name='labtest__CBL', lookup_expr='in')
    labtest__THCVA__in = CharInFilter(field_name='labtest__THCVA', lookup_expr='in')
    labtest__THCV__in = CharInFilter(field_name='labtest__THCV', lookup_expr='in')
    labtest__CBDV__in = CharInFilter(field_name='labtest__CBDV', lookup_expr='in')
    labtest__Total_THC__in = CharInFilter(field_name='labtest__Total_THC', lookup_expr='in')
    labtest__Total_CBD__in = CharInFilter(field_name='labtest__Total_CBD', lookup_expr='in')
    labtest__Box_Link__in = CharInFilter(field_name='labtest__Box_Link', lookup_expr='in')
    actual_available_stock = CharInFilter(field_name='actual_available_stock', lookup_expr='in')
    pre_tax_price = CharInFilter(field_name='pre_tax_price', lookup_expr='in')
    cf_date_available = django_filters.CharFilter(field_name ='cf_date_available',method='get_new_items', label='New Items')

    def get_new_items(self, queryset, name, value):
        items = queryset.annotate(
            full_date=ExpressionWrapper(
                F('cf_date_available') + timedelta(days=7),output_field=DateField())).filter(full_date__gt=timezone.now().date())
        return items
    
    def get_cultivars(self, queryset, name, value):
        items = queryset.filter(
            cf_strain_name__icontains=value).filter(cf_cfi_published=True)
        return items

    def get_nutrients(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,nutrients__overlap=value.split(','))
        return items
    
    def get_tags(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,tags__overlap=value.split(','))
        return items

    def get_ethics_and_certification(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,ethics_and_certification__overlap=value.split(','))
        return items

    def get_county_grown(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,county_grown__overlap=value.split(','))
        return items

    def get_appellation(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,appellation__overlap=value.split(','))
        return items
    
    def cf_strain_name__in(self, queryset, name, values):
        #items = queryset.filter(cf_cfi_published=True,cf_strain_name__in=values)
        items = queryset.filter(reduce(operator.or_, (Q(cf_strain_name__icontains=x) for x in values)))
        return items

    def category_name__in(self, queryset, name, values):
        items = queryset.filter(reduce(operator.or_, (Q(category_name__icontains=x) for x in values)))
        return items

    def cf_client_code__in(self, queryset, name, values):
        items = queryset.filter(reduce(operator.or_, (Q(cf_client_code__icontains=x) for x in values)))
        return items

    def get_cultivar_type(self, queryset, name, values):
        items = queryset.filter(reduce(operator.or_, (Q(cultivar__cultivar_type__icontains=x) for x in values)))
        return items
    
    def cf_cultivation_type__in(self, queryset, name, values):
        items = queryset.filter(reduce(operator.or_, (Q(cf_cultivation_type__icontains=x) for x in values)))
        return items
    
    def filter_cf_pesticide_summary__in(self, queryset, name, values):
        values = ['ND' if val == 'Non-Detect' else val for val in values ]
        queryset.select_related('labtest')
        pesticide_summary_fields = (
            'Acephate', 'Acequinocyl', 'Acetamiprid', 'Aldicarb', 'Azoxystrobin', 'Bifenazate',
            'Bifenthrin', 'Boscalid', 'Captan', 'Carbaryl', 'Carbofuran', 'Chlordane',
            'Chlorfenapyr', 'Chlorpyrifos', 'Chlortraniliprole', 'Clofentazine', 'Coumaphos',
            'Cyfluthrin', 'Cypermethrin', 'Daminozide', 'Diazinon', 'Dichlorvos', 'Dimethoate',
            'Dimethomorph', 'Ethoprop', 'Etofenprox', 'Etoxazole', 'Fenhexamid', 'Fenoxycarb',
            'Fenpyroximate', 'Fipronil', 'Flonicamid', 'Fludoxinil', 'Hexythiazox', 'Imazilil',
            'Imidacloprid', 'Kresoxim_methyl', 'Malathion', 'Metalaxyl', 'Methiocarb', 'Methomyl',
            'Mevinphos', 'Myclobutanil', 'Naled', 'Oxamyl', 'Paclobutrazole', 'Parathion_methyl',
            'Pentachloronitrobenzene', 'Permethrin', 'Phosmet', 'Piperonyl_butoxide', 'Prallethrin',
            'Propiconazole', 'Propoxur', 'Pyrethrins', 'Pyridaben', 'Spinatoram', 'Spinosad',
            'Spiromesifen', 'Spirotetramat', 'Spiroxamine', 'Tebuconazole', 'Thiacloprid',
            'Thiamethoxam', 'Trifloxystrobin',
        )
        q = Q(**{'labtest__'+x+'__in': values for x in pesticide_summary_fields}, _connector='AND')
        return queryset.filter(q).distinct()

    class Meta:
        model = Inventory
        fields = {
        'sku':['icontains', 'exact'],
        'category_name':['icontains', 'exact'],
        'vendor_name': ['icontains', 'exact'],
        'cf_vendor_name': ['icontains', 'exact'],
        'parent_category_name':['icontains', 'exact'],
        'cf_cultivar_type':['icontains', 'exact'],
        'price':['gte', 'lte', 'gt', 'lt'],
        'available_stock':['gte', 'lte', 'gt', 'lt'],
        'stock_on_hand':['gte', 'lte', 'gt', 'lt'],
        'cf_cannabis_grade_and_category':['icontains', 'exact'],
        'last_modified_time':['gte', 'lte', 'gt', 'lt'],
        'product_type':['icontains', 'exact'],
        'cf_pesticide_summary':['icontains', 'exact'],
        'cf_status':['icontains', 'exact'],
        'labtest__Box_Link':['icontains', 'exact'],
        'labtest__alpha_pinene':['icontains', 'exact'],
        'labtest__Myrcene':['icontains', 'exact'],
        'labtest__Ocimene':['icontains', 'exact'],
        'labtest__alpha_Terpineol':['icontains', 'exact'],
        'labtest__beta_Caryophyllene':['icontains', 'exact'],
        'labtest__alpha_Humulene':['icontains', 'exact'],
        'labtest__Linalool':['icontains', 'exact'],
        'labtest__R_Limonene':['icontains', 'exact'],
        'labtest__Terpinolene':['icontains', 'exact'],
        'labtest__Valencene':['icontains', 'exact'],
        'labtest__Geraniol':['icontains', 'exact'],
        'labtest__THC':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBD':['gte', 'lte', 'gt', 'lt'],
        'labtest__d_8_THC':['gte', 'lte', 'gt', 'lt'],
        'labtest__THCA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBDA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBN':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBC':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBCA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBGA':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBG':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBL':['gte', 'lte', 'gt', 'lt'],
        'labtest__THCVA':['gte', 'lte', 'gt', 'lt'],
        'labtest__THCV':['gte', 'lte', 'gt', 'lt'],
        'labtest__CBDV':['gte', 'lte', 'gt', 'lt'],
        'labtest__Total_Terpenes':['gte', 'lte', 'gt', 'lt'],    
        'cf_quantity_estimate': ['gte', 'lte', 'gt', 'lt'],
        'labtest__Total_THC':['gte', 'lte', 'gt', 'lt'],
        'labtest__Total_CBD':['gte', 'lte', 'gt', 'lt'],
        'actual_available_stock': ['gte', 'lte', 'gt', 'lt'],
        'pre_tax_price': ['gte', 'lte', 'gt', 'lt']
        }

class CustomOrderFilter(OrderingFilter):
    fields_related = {
        'Total_THC': 'labtest__Total_THC', # ForeignKey Field lookup for ordering
        'Box_Link': 'labtest__Box_Link',
        'Created_Time':'labtest__Created_Time',
        'Total_CBD': 'labtest__Total_CBD'
    }

    def get_valid_fields(self, queryset, view, context={}):
        valid_fields = super().get_valid_fields(queryset, view, context=context)
        valid_fields += [(field, ' '.join(field.split('_'))) for field in self.fields_related]
        return valid_fields


    def filter_queryset(self, request, queryset, view):
        order_fields = []
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            for field in ordering:
                if field[0] == '-':
                    f = field.lstrip('-')
                    order_fields.append(F(self.fields_related.get(f, f)).desc(nulls_last=True))
                else:
                    f = field.lstrip('+')
                    order_fields.append(F(self.fields_related.get(f, f)).asc(nulls_last=True))
        if order_fields:
            return queryset.order_by(*order_fields)

        return queryset


class BasicPagination(PageNumberPagination):
    """
    Pagination class.
    """
    #page_size_query_param = 'limit'
    page_size_query_param = 'page_size'
    page_size = 50


class InventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (InventoryPermission, )
    filter_backends = (CustomOrderFilter,filters.DjangoFilterBackend,)
    filterset_class = DataFilter
    ordering_fields = '__all__'
    pagination_class = BasicPagination
    ordering = ('-Created_Time',)
    
    def extract_positive_value_queryset(self, qs):
        """
        -Get positive quantity values only
        -For cf_status ['Pending Sale','Available','In-Testing'] get actual_available_stock > 0 values
        -For other cf_staus viz ['Vegging','Processing', 'Sold', 'Under Contract','Flowering','Return to Vendor',None] get cf_quantity_estimate > 0
        """
        available_stock_qs = qs.filter(cf_status__in=['Pending Sale','Available','In-Testing'],actual_available_stock__gt=0,cf_cfi_published=True)
        quantity_est_qs = qs.filter(cf_status__in=['Vegging','Processing', 'Sold', 'Under Contract','Flowering','Return to Vendor',None],cf_quantity_estimate__gt=0,cf_cfi_published=True)
        final_qs = available_stock_qs | quantity_est_qs
        return final_qs
    
    def get_serializer_class(self):
        """
        Return serializer.
        """
        if not self.request.user.is_authenticated:
            return LogoutInventorySerializer
        return InventorySerializer

    def get_queryset(self):
        """
        Return QuerySet.
        Note: Can reduce qs (one step for positive values) but if someone adds new cf_status to inv items,
        then few items might be missed from list so keeping these two step qs.
        """
        qs = Inventory.objects.filter(status='active',cf_cfi_published=True)
        return self.extract_positive_value_queryset(qs)

    def list(self, request):
        """
        Return inventory list queryset with summary.
        """
        page_size = request.query_params.get('page_size', 50)
        statuses = request.query_params.get('cf_status__in')
        summary = self.filter_queryset(self.get_queryset())
        summary = get_inventory_summary(summary, statuses)
        params = dict()
        for k, v in request.query_params.items():
            if k not in ['cf_status__in', 'order-by', 'page', 'page_size'] and v:
                params[k] = v
        category_count = get_category_count(params)
        queryset = Paginator(self.filter_queryset(self.get_queryset()), page_size)
        page = int(request.query_params.get('page', 1))
        if page > queryset.num_pages:
            return Response({
                "status": "Result only have {} number of pages".format(applicants.num_pages)
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset.page(page), many=True)
        data = {}
        data['meta'] = {
            "number_of_pages": queryset.num_pages,
            "page": page,
            "number_of_records": queryset.count,
            "page_size": page_size
        }
        data['summary'] = summary
        data['categories_count'] = category_count
        data['results'] = serializer.data
        return Response(data)

    # def put(self, request):
    #     """
    #     Update inventory item.
    #     """
    #     is_update_zoho = request.query_params.get('is_update_zoho', False)
    #     item = request.data
    #     inventory_name = 'inventory_efd' if item.get('inventory_name') == 'EFD' else 'inventory_efl'
    #     item.pop('inventory_name')
    #     if item.get('labtest'):
    #         obj = LabTest.objects.update_or_create(id=item.get('labtest').get('id'), defaults=item.get('labtest'))
    #         item.pop('labtest')
    #     if item.get('cultivar'):
    #         obj = Cultivar.objects.update_or_create(id=item.get('cultivar').get('id'), defaults=item.get('cultivar'))
    #         item.pop('cultivar')
    #     obj = Inventory.objects.update_or_create(item_id=item.get('item_id'), defaults=item)
    #     if is_update_zoho:
    #         response = update_inventory_item(inventory_name, item.get('item_id'), item)
    #         return Response(response)
    #     return Response(item)

class InventoryWebHook(APIView):
    """
    Inventory web hook for zoho crm.
    """
    authentication_classes = (TokenAuthentication, )

    def put(self, request):
        """
        Update inventory item.
        """
        is_update_zoho = request.query_params.get('is_update_zoho', False)
        item = request.data
        inventory_name = 'inventory_efd' if item.get('inventory_name') == 'EFD' else 'inventory_efl'
        obj = Inventory.objects.update_or_create(item_id=item.get('item_id'), defaults=item)
        if is_update_zoho:
            response = update_inventory_item(inventory_name, item.get('item_id'), item)
            return Response(response)
        return Response(item)


class ItemFeedbackViewSet(viewsets.ModelViewSet):
    """
    Item Feedback View
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = '__all__'

    def get_serializer_class(self):
        """
        Return serializer.
        """
        return ItemFeedbackSerializer

    def get_queryset(self):
        """
        Return QuerySet.
        """
        return ItemFeedback.objects.all()


class InventorySyncView(APIView):
    """
    Real time inventory sync.
    """
    authentication_classes = (TokenAuthentication, )

    def post(self, request):
        """
        Post realtime inventory updates.
        """
        record = sync_inventory(
            request.data.get('inventory_name'),
            request.data.get('JSONString'))
        return Response(record)




class CategoryNameView(APIView):
    """
    Return distinct category_name
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Return QuerySet.
        """
        if request.query_params.get('category_name'):
            categories = Inventory.objects.filter(
                status='active',
                cf_cfi_published=True,
                category_name__icontains=request.query_params.get('category_name')
                ).values('category_name').distinct()
        else:
            categories = Inventory.objects.filter(
                status='active',
                cf_cfi_published=True,
                ).values('category_name').distinct()
        return Response({
            'status_code': 200,
            'response': [{
                'label': i['category_name'],
                'value': i['category_name']} for i in categories if i['category_name'] != None]})
    
class CultivarCategoryView(APIView):
    """
    Return distinct cultivar categroies.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Return QuerySet.
        """
        if request.query_params.get('cultivar_name'):
            categories = Inventory.objects.filter(
                cf_cfi_published=True,
                cf_strain_name__icontains=request.query_params.get('cultivar_name')
                ).values('cf_strain_name').distinct()
        else:
            categories = Inventory.objects.filter(
                cf_cfi_published=True,
                ).values('cf_strain_name').distinct()
        return Response({
            'status_code': 200,
            'response': [{
                'label': i['cf_strain_name'],
                'value': i['cf_strain_name']} for i in categories if i['cf_strain_name'] != None]})

class CultivarTypesView(APIView):
    """
    Return distinct cultivar types.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Return distinct cultivar types.
        """
        categories = Cultivar.objects.filter(
                ).values('cultivar_type').distinct()
        return Response({
            'status_code': 200,
            'response': [{
                'label': i['cultivar_type'],
                'value': i['cultivar_type']} for i in categories if i['cultivar_type'] != None]})
    
    
class InventoryClientCodeView(APIView):
    """
    Return distinct client code
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Return QuerySet.
        """
        if request.query_params.get('cf_client_code'):
            items = Inventory.objects.filter(
                cf_cfi_published=True,
                cf_client_code__icontains=request.query_params.get('cf_client_code')
                ).values('cf_client_code').distinct()
        else:
            items = Inventory.objects.filter(
                cf_cfi_published=True,
                ).values('cf_client_code').distinct()
        return Response({
            'status_code': 200,
            'response': [{
                'label': i['cf_client_code'],
                'value': i['cf_client_code']} for i in items if i['cf_client_code'] != None]})    

class InventoryCultivationTypeView(APIView):
    """
    Return distinct cultivation type
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Return QuerySet.
        """
        if request.query_params.get('cf_cultivation_type'):
            items = Inventory.objects.filter(
                cf_cfi_published=True,
                cf_cultivation_type__icontains=request.query_params.get('cf_cultivation_type')
                ).values('cf_cultivation_type').distinct()
        else:
            items = Inventory.objects.filter(
                cf_cfi_published=True,
                ).values('cf_cultivation_type').distinct()
        return Response({
            'status_code': 200,
            'response': [{
                'label': i['cf_cultivation_type'],
                'value': i['cf_cultivation_type']} for i in items if i['cf_cultivation_type'] != None]})

    
class InventoryStatusTypeView(APIView):
    """
    Return distinct status types.
    """
    def get(self, request):
        """
        Return distinct status types.
        """
        categories = Inventory.objects.filter(
                cf_cfi_published=True
                ).values('cf_status').distinct()
        return Response({
            'status_code': 200,
            'response': [i['cf_status'] for i in categories]})


class InventoryUpdateDateView(APIView):
    """
    Return inventory update date.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Return inventory update date.
        """
        items = Inventory.objects.filter(
            cf_cfi_published=True).order_by('-last_modified_time')
        if items.exists():
            return Response({
                'last_modified_time': items.first().last_modified_time},
            status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class InTransitOrderViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = InTransitOrderSerializer
    queryset = InTransitOrder.objects.all()
    lookup_field = 'profile_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset #.filter(user=self.request.user)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        obj, created = queryset.model.objects.get_or_create(**filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def destroy(self, request, *args, **kwargs):
        """
        Method to add some more customization related to bills(Estimate removal)
        """

        obj = self.get_object()
        remove_estimates_after_intransit_clears.delay(obj.profile_id) 
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PendingOrderAdminView(APIView):
    """
    View to save pending order that will reflect in admin 
    """
    permission_classes = (IsAuthenticated, )

    def put(self, request, **kwargs):
        
        try:
            in_transit_data = parse_intransit_to_pending(request.data)
        except Exception as e:
            print('exception while parsint intransit to pending', e)
            
        if in_transit_data:
            response = parse_fields('estimate', in_transit_data)
            sign_url = None
            estimate = response
            line_items = in_transit_data.get('line_items',[])
            line_items = parse_fields('item', line_items, many=True)
            estimate_obj = save_estimate_from_intransit(in_transit_data)
            return Response(estimate, status=status.HTTP_200_OK)
        return Response({'error': 'something went wrong while saving pending/estimate data'},status=status.HTTP_400_BAD_REQUEST)
         
    
class DocumentPreSignedView(APIView):
    """
    Document pre signed view class.
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """
        Get pre-signed url.
        """
        object_name = request.query_params.get('object_name')
        expiry = request.query_params.get('expiration')
        response = create_presigned_url(AWS_BUCKET, object_name, expiry)
        if response.get('status_code') != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Get pre-signed post url.
        """
        sku = request.data.get('sku')
        license_id = request.data.get('license_id')
        object_name = request.data.get('object_name')
        user_id = request.data.get('user_id')
        brand_id = request.data.get('brand_id')
        organization_id = request.data.get('organization_id')
        doc_type = request.data.get('doc_type')
        custom_inventory_id = request.data.get('custom_inventory_id')
        expiry = request.data.get('expiration', 3600)
        if sku:
            try:
                obj = Inventory.objects.get(sku=sku)
            except Inventory.DoesNotExist:
                return Response({'error': 'Item not in database'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif user_id:
            try:
                obj = User.objects.get(id=user_id)
            except Inventory.DoesNotExist:
                return Response({'error': 'User not in database'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif brand_id:
            try:
                obj = Brand.objects.get(id=brand_id)
            except Inventory.DoesNotExist:
                return Response({'error': 'Brand not in database'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif custom_inventory_id:
            try:
                obj = CustomInventory.objects.get(id=custom_inventory_id)
            except CustomInventory.DoesNotExist:
                return Response({'error': 'Custom inventory not in database'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif organization_id:
            try:
                obj = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return Response({'error': 'License not in database'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                obj = License.objects.get(id=license_id)
            except License.DoesNotExist:
                return Response({'error': 'License not in database'},
                                status=status.HTTP_400_BAD_REQUEST)
        mime = MimeTypes()
        mime_type, _ = mime.guess_type(object_name)
        obj = Documents(content_object=obj,
                        sku=sku, name=object_name,
                        file_type=mime_type, doc_type=doc_type)
        obj.save()
        if sku:
            path = f'inventory/{sku}/{obj.id}/{object_name}'
        else:
            path = object_name
        obj.path = path
        obj.save()
        response = create_presigned_post(AWS_BUCKET, path, expiry)
        if response.get('status_code') != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        response['document_id'] = obj.id
        return Response(response, status=status.HTTP_201_CREATED)


class DocumentView(APIView):
    """
    Document view class.
    """
    permission_classes = (DocumentPermission, )

    def get(self, request, *args, **kwargs):
        """
        Get document.
        """
        id = kwargs.get('id', None)
        sku = request.query_params.get('sku', None)
        display = request.query_params.get('display', None)
        if id:
            data = Documents.objects.filter(id=id, status='AVAILABLE').order_by('file_type').values()
            return Response(
                data,
                status=status.HTTP_200_OK
            )
        elif sku:
            if display == 'all':
                data_1 = Documents.objects.filter(sku=sku, status='OPTIMIZING').order_by('file_type').values()
                data_2 = Documents.objects.filter(sku=sku, status='AVAILABLE').order_by('file_type').values()
                data_3 = data_1 | data_2
            else:
                data_3 = Documents.objects.filter(sku=sku, status='AVAILABLE').order_by('file_type').values()
            return Response(
                data_3.order_by('order', 'status'),
                status=status.HTTP_200_OK
            )
        return Response(
            Documents.objects.values(),
            status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """
        Update document fields.
        """
        id = kwargs.get('id', None)
        try:
            if request.data.get('is_primary'):
                main_doc = Documents.objects.get(id=id)
                documents = Documents.objects.filter(sku=main_doc.sku).update(is_primary=False)
                box_id = main_doc.box_id
                item_id = main_doc.object_id
                file_obj = get_file_obj(box_id)
                file_ = file_obj.content()
                file_ = BufferedReader(BytesIO(file_))
                inventory_name = get_inventory_name(item_id)
                response = upload_inventory_document(inventory_name, item_id, {
                    'image': (
                        file_obj.name,
                        file_,
                        main_doc.file_type)})
                if response.get('code') != 0:
                    print(response)
            obj, _ = Documents.objects.update_or_create(
                        id=id,
                        defaults=request.data)
            return Response(status=status.HTTP_202_ACCEPTED)
        except Documents.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        Delete document.
        """
        id = kwargs.get('id', None)
        if id:
            document = Documents.objects.get(id=id)
            delete_file(document.box_id)
            document.delete()
            return Response(
                {'status': 'Success'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'status': 'Failure'},
            status=status.HTTP_400_BAD_REQUEST)


class DocumentStatusView(APIView):
    """
    Document view class.
    """
    authentication_classes = (TokenAuthentication, )

    def put(self, request, *args, **kwargs):
        """
        Update document fields.
        """
        id = kwargs.get('id', None)
        try:
            obj, created = Documents.objects.update_or_create(
                    id=id,
                    defaults=request.data)
            if request.data.get('thumbnail_url') and request.data.get('mobile_url') and obj.is_primary:
                try:
                    item = Inventory.objects.get(item_id=obj.object_id)
                    item.thumbnail_url = request.data.get('thumbnail_url')
                    item.mobile_url = request.data.get('mobile_url')
                    item.save()
                except Inventory.DoesNotExist:
                    return Response({}, status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_202_ACCEPTED)
        except Documents.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class InventoryDeleteView(APIView):
    """
    Delete inventory item.
    """
    authentication_classes = (TokenAuthentication, )

    def delete(self, request, *args, **kwargs):
        """
        Delete item.
        """
        item_id = kwargs.get('item_id', None)
        if item_id:
            try:
                Inventory.objects.get(item_id=item_id).delete()
                return Response(
                    {'status': 'success'},
                    status=status.HTTP_200_OK
                )
            except Inventory.DoesNotExist:
                pass
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class InventoryCountyView(APIView):
    """
    Return Inventory county.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Get inventory county.
        """
        categories = Inventory.objects.filter(cf_cfi_published=True).values_list('county_grown',flat=True).distinct()
        clean_counties = list(filter(None,list(categories)))
        return Response({
            'status_code': 200,
            'response': list(set([item for sublist in clean_counties for item in sublist]))})

class InventoryAppellationView(APIView):
    """
    Return Inventory Appellation.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Get inventory appellation
        """
        categories = Inventory.objects.filter(cf_cfi_published=True).values_list('appellation',flat=True).distinct()
        clean_appellation = list(filter(None,list(categories)))
        return Response({
            'status_code': 200,
            'response': list(set([item for sublist in clean_appellation for item in sublist]))})
    
class InventoryNutrientsView(APIView):
    """
    Return Inventory nutrients.
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Get inventory nutrients.
        """
        nutrients = Inventory.objects.filter(cf_cfi_published=True).values_list('nutrients',flat=True).distinct()
        clean_nutrients = list(filter(None,list(nutrients)))
        return Response({
            'status_code': 200,
            'response':list(set([item for sublist in clean_nutrients for item in sublist]))})

class InventoryTagsView(APIView):
    """
    Return Inventory tags
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Get inventory tags
        """
        response = get_inventory_metadata('inventory_efd')
        dynamic_tags = list(filter(lambda tags: tags['label'] == 'Tags', response['custom_fields']))
        return Response({
            'status_code': 200,
            'response': [val['name'] for val in dynamic_tags[0]['values']]})
    
class InventoryEthicsView(APIView):
    """
    Return Inventory ethics & certifications
    """
    permission_classes = (AllowAny, )

    def get(self, request):
        """
        Get inventory ethics & certifications
        """
        ethics = Inventory.objects.filter(cf_cfi_published=True).values_list('ethics_and_certification',flat=True).distinct()
        clean_ethics = list(filter(None,list(ethics)))
        return Response({
            'status_code': 200,
            'response': list(set([item for sublist in clean_ethics for item in sublist]))})


class CustomInventoryFilterSet(FilterSet):
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    class Meta:
        model = CustomInventory
        fields = {
            'status':['icontains', 'exact'],
            'vendor_name':['icontains', 'exact'],
        }

class CustomInventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend,)
    filterset_class = CustomInventoryFilterSet
    ordering_fields = '__all__'
    pagination_class = BasicPagination
    ordering = ('created_on',)
    serializer_class = CustomInventorySerializer

    def get_queryset(self):
        """
         Return QuerySet.
        """
        return CustomInventory.objects.all()

    def perform_create(self, serializer):
        obj = serializer.save()
        user = serializer.context['request'].user
        obj.created_by = {
            'email': user.email,
            'phone': user.phone.as_e164,
            'name':  user.get_full_name(),
        }
        obj.save()
        get_custom_inventory_data_from_crm_task(obj.id)
        notify_inventory_item_submitted_task.delay(obj.id)
        create_duplicate_crm_vendor_from_crm_account_task.delay(obj.id)


class InventoryExportViewSet(viewsets.ModelViewSet):
    """
    Inventory  Ecport View
    """
    permission_classes = (InventoryPermission, )
    filter_backends = (CustomOrderFilter,filters.DjangoFilterBackend,)
    filterset_class = DataFilter
    ordering_fields = '__all__'
    ordering = ('-Created_Time',)
    pagination_class = None

    def get_serializer_class(self):
        """
        Return serializer.
        """
        if not self.request.user.is_authenticated:
            return LogoutInventorySerializer
        return InventorySerializer

    def get_queryset(self):
        """
         Return QuerySet.
        """
        return Inventory.objects.filter(cf_cfi_published=True)

    def list(self, request):
        """
        Return inventory list queryset with summary for export.
        """
        data = dict()
        summary = self.filter_queryset(self.get_queryset())
        statuses = request.query_params.get('cf_status__in')
        summary = get_inventory_summary(summary, statuses)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data['summary'] = summary
        data['results'] = serializer.data
        return Response(data)


class InventoryItemEditFilterSet(FilterSet):
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    class Meta:
        model = InventoryItemEdit
        fields = {
            'status':['icontains', 'exact'],
        }


class InventoryItemEditViewSet(mixins.CreateModelMixin,
                                         mixins.RetrieveModelMixin,
                                        #  mixins.UpdateModelMixin,
                                         mixins.DestroyModelMixin,
                                         mixins.ListModelMixin,
                                         GenericViewSet):
    """
    ViewSet
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend,)
    filterset_class = InventoryItemEditFilterSet
    ordering_fields = '__all__'
    pagination_class = BasicPagination
    ordering = ('created_on',)
    serializer_class = InventoryItemEditSerializer
    queryset = InventoryItemEdit.objects.all()



    def perform_create(self, serializer):
        obj = serializer.save()
        user = serializer.context['request'].user
        obj.created_by = {
            'email': user.email,
            'phone': user.phone.as_e164,
            'name':  user.get_full_name(),
        }
        obj.save()
        notify_inventory_item_change_submitted_task.delay(obj.id)


class InventoryItemQuantityAdditionFilterSet(FilterSet):
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    class Meta:
        model = InventoryItemEdit
        fields = {
            'status':['icontains', 'exact'],
        }


class InventoryItemQuantityAdditionViewSet(mixins.CreateModelMixin,
                                         mixins.RetrieveModelMixin,
                                        #  mixins.UpdateModelMixin,
                                         mixins.DestroyModelMixin,
                                         mixins.ListModelMixin,
                                         GenericViewSet):
    """
    ViewSet
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend,)
    filterset_class = InventoryItemQuantityAdditionFilterSet
    ordering_fields = '__all__'
    pagination_class = BasicPagination
    ordering = ('created_on',)
    serializer_class = InventoryItemQuantityAdditionSerializer
    queryset = InventoryItemQuantityAddition.objects.all()


    def perform_create(self, serializer):
        obj = serializer.save()
        user = serializer.context['request'].user
        obj.created_by = {
            'email': user.email,
            'phone': user.phone.as_e164,
            'name':  user.get_full_name(),
        }
        obj.save()
        inventory_item_quantity_addition_task.delay(obj.id)

class InventoryItemDelistFilterSet(FilterSet):
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    class Meta:
        model = InventoryItemDelist
        fields = {
            'status':['icontains', 'exact'],
            'item_id':['exact',],
        }


class InventoryItemDelistViewSet(mixins.CreateModelMixin,
                                         mixins.RetrieveModelMixin,
                                        #  mixins.UpdateModelMixin,
                                         mixins.DestroyModelMixin,
                                         mixins.ListModelMixin,
                                         GenericViewSet):
    """
    ViewSet
    """
    permission_classes = (IsAuthenticated, )
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend,)
    filterset_class = InventoryItemDelistFilterSet
    ordering_fields = '__all__'
    pagination_class = BasicPagination
    ordering = ('created_on',)
    serializer_class = InventoryItemDelistSerializer
    queryset = InventoryItemDelist.objects.all()

    def perform_create(self, serializer):
        obj = serializer.save()
        user = serializer.context['request'].user
        obj.created_by = {
            'email': user.email,
            'phone': user.phone.as_e164,
            'name':  user.get_full_name(),
        }
        obj.save()
        notify_inventory_item_delist_submitted_task.delay(obj.id)

class PackageView(APIView):
    """
    View class for Zoho inventory packages.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get/List packages.
        """
        organization_name = request.query_params.get('organization_name')
        if request.query_params.get('package_id', None):
            response = get_packages(
                organization_name,
                request.query_params.get('package_id'),
                params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        response = get_packages(organization_name, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)
    
    def put(self, request):
        """
        Update package.
        """
        organization_name = request.query_params.get('organization_name')
        package_id = request.data['package_id']
        response = update_package(organization_name, package_id=package_id, data=request.data, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)


class SalesReturnView(APIView):
    """
    View class for Zoho inventory sales return.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get/List sales return.
        """
        organization_name = request.query_params.get('organization_name')
        if request.query_params.get('sales_return_id', None):
            response = get_sales_returns(
                organization_name,
                request.query_params.get('sales_return_id'),
                params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        response = get_sales_returns(organization_name, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)
    
    def put(self, request):
        """
        Update sales return.
        """
        organization_name = request.query_params.get('organization_name')
        salesreturn_id = request.data['salesreturn_id']
        response = update_sales_return(organization_name, salesreturn_id=salesreturn_id, data=request.data, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)

class ContactView(APIView):
    """
    View class for Zoho inventory contact.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get/List contacts.
        """
        organization_name = request.query_params.get('organization_name')
        if request.query_params.get('contact_id', None):
            response = get_contacts(
                organization_name,
                request.query_params.get('contact_id'),
                params=request.query_params.dict())
            if response.get('code') and response['code'] != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return Response(response, status=status.HTTP_200_OK)
        response = get_contacts(organization_name, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)
    
    def put(self, request):
        """
        Update contact.
        """
        organization_name = request.query_params.get('organization_name')
        contact_id = request.data['contact_id']
        response = update_contact(organization_name, package_id=package_id, data=request.data, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)

class InventoryMetaDataView(APIView):
    """
    View class for Zoho inventory metadata.
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """
        Get inventory meta data.
        """
        organization_name = request.query_params.get('organization_name')
        response = get_inventory_metadata(organization_name, params=request.query_params.dict())
        if response.get('code') and response['code'] != 0:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)

class ConvertSalesOrderToPackage(APIView):
    """
    View class to convert Sales order to package.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Convert document.
        """
        organization_name = request.query_params.get('organization_name')
        sales_order_id = request.data.get('salesorder_id')
        if sales_order_id:
            books_name = get_books_name_from_inventory_name(organization_name)
            so = get_salesorder(books_name, so_id=sales_order_id, params={})
            so = parse_book_object('package', so, line_item_parser='salesorder_parser')
            print(so)
            package = create_package(organization_name, so)
            if package.get('code') != 0:
                return Response(package, status=status.HTTP_400_BAD_REQUEST)
            return Response(package)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class InTransitDeleteSyncView(APIView):
    """
    Removes Intransit items.
    """
    authentication_classes = (TokenAuthentication, )

    def post(self, request):
        """
        Remove intransit items
        """
        estimate_id = request.data.get('estimate_id')
        if estimate_id:
            delete_in_transit_item(estimate_id)
            return Response({"In Transit order item removed successfully for estimate_id %s " % estimate_id},status=status.HTTP_200_OK)
        return Response({"Something went wrong!"}, status=status.HTTP_400_BAD_REQUEST)        

class InventoryUpdateView(APIView):
    """
    Inventory item update in inventory.
    """
    permission_classes = (InventoryPermission, )

    def put(self, request):
        """
        Update inventory item in DB & ZOHO.
        tags: Field in DB
        cf_tags: Field in zoho
        """
        item = request.data
        if item.get('item_id'):
            obj = Inventory.objects.update_or_create(item_id=item.get('item_id'), defaults=item)
            item['cf_tags'] = item.pop('tags') #Added cf_tags insted of tags
            inventory_name = get_inventory_name(item.get('item_id'))
            response = async_update_inventory_item.delay(inventory_name,item.get('item_id'), item)
            return Response({"Item Updated Successfully!"},status=status.HTTP_200_OK)
        return Response({"item_id is missing!"}, status=status.HTTP_400_BAD_REQUEST)        


    
