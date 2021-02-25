"""
Views for Inventory
"""
from io import BytesIO, BufferedReader
from mimetypes import MimeTypes
import django_filters
from django.shortcuts import (render, )
from django.db.models import (Sum, F, Min, Max, Avg, Q)
from rest_framework.views import APIView
from rest_framework.response import (Response, )
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework import (viewsets, status,)
from rest_framework.filters import (OrderingFilter, )
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from django.shortcuts import get_object_or_404

from django.core.paginator import Paginator
from core.pagination import PageNumberPagination
from .serializers import (InventorySerializer, LogoutInventorySerializer,
                          ItemFeedbackSerializer, InTransitOrderSerializer,
                          CustomInventorySerializer,)
from .models import (Inventory, ItemFeedback, InTransitOrder, Documents, CustomInventory)
from core.settings import (AWS_BUCKET,)
from integration.inventory import (sync_inventory, upload_inventory_document,
                                   get_inventory_name)
from integration.apps.aws import (create_presigned_url, create_presigned_post)
from .permissions import (DocumentPermission, )
from integration.box import (delete_file, get_file_obj,)
from brand.models import (License, Brand, LicenseProfile)
from user.models import (User, )
from labtest.models import (LabTest, )
from integration.inventory import (get_inventory_summary,)
from .tasks import (notify_inventory_item_added, create_duplicate_crm_vendor_from_crm_account_task, )
class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):   
    name__in = CharInFilter(field_name='name', lookup_expr='in')
    product_type__in = CharInFilter(field_name='product_type', lookup_expr='in')
    cf_cultivar_type__in = CharInFilter(field_name='cf_cultivar_type', lookup_expr='in')
    vendor_name__in = CharInFilter(field_name='vendor_name', lookup_expr='in')
    cf_vendor_name__in = CharInFilter(field_name='cf_vendor_name', lookup_expr='in')
    county_grown__in = CharInFilter(field_name='county_grown', lookup_expr='in')
    cf_cannabis_grade_and_category__in = CharInFilter(field_name='cf_cannabis_grade_and_category', lookup_expr='in')
    # cf_pesticide_summary__in = CharInFilter(field_name='cf_pesticide_summary', lookup_expr='in')
    cf_pesticide_summary__in = CharInFilter(method='filter_cf_pesticide_summary__in', lookup_expr='in')
    cf_testing_type__in = CharInFilter(field_name='cf_testing_type', lookup_expr='in')
    cf_status__in = CharInFilter(field_name='cf_status', lookup_expr='in')
    cf_quantity_estimate__in = CharInFilter(field_name='cf_quantity_estimate', lookup_expr='in')
    cultivar = django_filters.CharFilter(method='get_cultivars')
    nutrients = django_filters.CharFilter(method='get_nutrients')
    ethics_and_certification = django_filters.CharFilter(method='get_ethics_and_certification')
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

    def get_cultivars(self, queryset, name, value):
        items = queryset.filter(
            cf_strain_name__icontains=value).filter(cf_cfi_published=True)
        return items

    def get_nutrients(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,nutrients__overlap=[value])
        return items

    def get_ethics_and_certification(self, queryset, name, value):
        items = queryset.filter(cf_cfi_published=True,ethics_and_certification__overlap=[value])
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
        'county_grown':['icontains', 'exact'],   
        'cf_strain_name':['icontains', 'exact'],
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
    permission_classes = (AllowAny, )
    filter_backends = (CustomOrderFilter,filters.DjangoFilterBackend,)
    filterset_class = DataFilter
    ordering_fields = '__all__'
    pagination_class = BasicPagination
    ordering = ('-Created_Time',)

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
        Return inventory list queryset with summary.
        """
        page_size = request.query_params.get('page_size', 50)
        summary = self.filter_queryset(self.get_queryset())
        summary = get_inventory_summary(summary)
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
        data['results'] = serializer.data
        return Response(data)


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
        return queryset.filter(user=self.request.user)

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
        print(filter_kwargs)

        obj, created = queryset.model.objects.get_or_create(user=self.request.user, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


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
            if request.data.get('thumbnail_url') and obj.is_primary:
                try:
                    item = Inventory.objects.get(item_id=obj.object_id)
                    item.thumbnail_url = request.data.get('thumbnail_url')
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
        categories = Inventory.objects.filter(
                cf_cfi_published=True
                ).values('county_grown').distinct()
        return Response({
            'status_code': 200,
            'response': [i['county_grown'] for i in categories if i['county_grown'] != None]})

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
            'response':list(set([item for sublist in clean_ethics for item in sublist]))})


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
        notify_inventory_item_added.delay(user.email, obj.id)
        create_duplicate_crm_vendor_from_crm_account_task(obj.vendor_name)
