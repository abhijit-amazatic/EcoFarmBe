"""
Views for Inventory
"""
from io import BytesIO, BufferedReader
from mimetypes import MimeTypes
import django_filters
from django.shortcuts import (render, )
from django.db.models import (Sum, F, Min, Max, Avg)
from rest_framework.views import APIView
from rest_framework.response import (Response, )
from rest_framework.authentication import (TokenAuthentication, )
from rest_framework import (viewsets, status,)
from rest_framework.filters import (OrderingFilter, )
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from django_filters import rest_framework as filters
from django_filters import (BaseInFilter, CharFilter, FilterSet)
from .serializers import (InventorySerializer, LogoutInventorySerializer,
                          ItemFeedbackSerializer, InTransitOrderSerializer)
from .models import (Inventory, ItemFeedback, InTransitOrder, Documents)
from core.settings import (AWS_BUCKET,)
from integration.inventory import (sync_inventory, upload_inventory_document,
                                   get_inventory_name)
from integration.apps.aws import (create_presigned_url, create_presigned_post)
from .permissions import (DocumentPermission, )
from integration.box import (delete_file, get_file_obj,)
from brand.models import (License, Brand, LicenseProfile)
from user.models import (User, )

class CharInFilter(BaseInFilter,CharFilter):
    pass

class DataFilter(FilterSet):   
    name__in = CharInFilter(field_name='name', lookup_expr='in')
    product_type__in = CharInFilter(field_name='product_type', lookup_expr='in')
    cf_cultivar_type__in = CharInFilter(field_name='cf_cultivar_type', lookup_expr='in')
    cf_cannabis_grade_and_category__in = CharInFilter(field_name='cf_cannabis_grade_and_category', lookup_expr='in')
    cf_pesticide_summary__in = CharInFilter(field_name='cf_pesticide_summary', lookup_expr='in')
    cf_testing_type__in = CharInFilter(field_name='cf_testing_type', lookup_expr='in')
    cf_status__in = CharInFilter(field_name='cf_status', lookup_expr='in')
    cf_quantity_estimate__in = CharInFilter(field_name='cf_quantity_estimate', lookup_expr='in')
    cultivar = django_filters.CharFilter(method='get_cultivars')
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
    
    class Meta:
        model = Inventory
        fields = {
        'sku':['icontains', 'exact'],
        'category_name':['icontains', 'exact'],
        'cf_cultivar_type':['icontains', 'exact'],
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
    allowed_custom_filters = ['Total_THC', 'Total_CBD', 'Box_Link']
    fields_related = {
        'Total_THC': 'labtest__Total_THC', # ForeignKey Field lookup for ordering
        'Box_Link': 'labtest__Box_Link', 
        'Total_CBD': 'labtest__Total_CBD'
    }
    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = [f for f in fields if f.lstrip('-') in self.allowed_custom_filters]
            if ordering:
                return ordering

        return self.get_default_ordering(view)

    def filter_queryset(self, request, queryset, view):
        order_fields = []
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            for field in ordering:
                symbol = "-" if "-" in field else ""
                order_fields.append(symbol+self.fields_related[field.lstrip('-')])
        if order_fields:
            return queryset.order_by(*order_fields)

        return queryset

class InventoryViewSet(viewsets.ModelViewSet):
    """
    Inventory View
    """
    permission_classes = (AllowAny, )
    filter_backends = (filters.DjangoFilterBackend,OrderingFilter,CustomOrderFilter)
    filterset_class = DataFilter
    ordering_fields = '__all__'
    
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
        if id:
            data = Documents.objects.filter(id=id, status='AVAILABLE').order_by('file_type').values()
            return Response(
                data,
                status=status.HTTP_200_OK
            )
        elif sku:
            data_1 = Documents.objects.filter(sku=sku, status='OPTIMIZING').order_by('file_type').values()
            data_2 = Documents.objects.filter(sku=sku, status='AVAILABLE').order_by('file_type').values()
            data_3 = data_1 | data_2
            return Response(
                data_3.order_by('status'),
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
                documents = Documents.objects.filter(sku=main_doc.sku)
                for doc in documents:
                    if doc.id != id:
                        doc.is_primary = False
                        doc.save()
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
            obj = Documents.objects.update_or_create(
                    id=id,
                    defaults=request.data)
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
    
class InventorySummaryView(APIView):
    """
    Return Inventory summary.
    """
    permission_classes = (IsAuthenticated, )
    
    def get(self, request):
        """
        Get inventory summary.
        """
        response = dict()
        inventory = Inventory.objects.filter(cf_status='Available')
        response['total_quantity'] = inventory.aggregate(Sum('actual_available_stock'))['actual_available_stock__sum']
        response['total_value'] = inventory.filter(
            category_name__contains='Flower').aggregate(
                total=Sum(F('actual_available_stock')*F('pre_tax_price')))['total']
        for category in ['Tops', 'Smalls', 'Trim']:
            response[category.lower() + '_quantity'] = inventory.filter(
                cf_cannabis_grade_and_category__contains=category).aggregate(
                    Sum('actual_available_stock'))['actual_available_stock__sum']
        response['average'] = inventory.aggregate(Avg('pre_tax_price'))['pre_tax_price__avg']
        return Response(response)