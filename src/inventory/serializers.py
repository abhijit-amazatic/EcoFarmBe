"""
Serializer for inventory
"""
import json
from rest_framework import serializers
from django.utils import timezone
from integration.apps.aws import (create_presigned_url, )
from permission.filterqueryset import (filterQuerySet, )
from brand.models import LicenseProfile
from cultivar.models import Cultivar
from core.settings import (AWS_BUCKET, )
from .models import (
    Inventory,
    CustomInventory,
    ItemFeedback,
    InTransitOrder,
    Documents,
    InventoryItemEdit,
    InventoryItemQuantityAddition,
    InventoryItemDelist,
)
from .data import CG

class InventorySerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    class Meta:
        model = Inventory
        depth = 1
        exclude = ()
        
class LogoutInventorySerializer(serializers.ModelSerializer):
    """
    Logout serializer.
    """
    class Meta:
        model = Inventory
        depth = 1
        fields = (
            'created_time',
            'item_id',
            'cf_strain_name',
            'cf_cultivation_type',
            'cf_cannabis_grade_and_category',
            'available_stock',
            'category_name',
            'sku',
            'cf_status',
            'cf_quantity_estimate',
            'actual_available_stock',
            'documents',
            'cultivar',
            'labtest',
            'cf_date_available',
            'tags',
            'thumbnail_url')
        
class ItemFeedbackSerializer(serializers.ModelSerializer):
    """
    User item feedback serializer.
    """
    class Meta:
        model = ItemFeedback
        fields = ('__all__')

class InTransitOrderSerializer(serializers.ModelSerializer):
    """
    User item feedback serializer.
    """
    order_data = serializers.JSONField(allow_null=False)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        try:
            instance = InTransitOrder.objects.get(
                profile_id=validated_data['profile_id']
            )
            if not instance.order_data:
                instance.created_on = timezone.now()
            return super().update(instance, validated_data)
        except InTransitOrder.DoesNotExist:
            return super().create(validated_data)


    def validate_order_data(self, value):
        if value is None:
            raise serializers.ValidationError('This field may not be null.', code=400)
        return value

    class Meta:
        model = InTransitOrder
        fields = ('profile_id', 'order_data', 'created_on', 'updated_on')
        read_only_fields = ('created_on', 'updated_on')


class CustomInventoryCultivarNameField(serializers.RelatedField):
    queryset = Cultivar.objects.all()

    def to_representation(self, obj):
        return obj.cultivar_name

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        queryset = queryset.filter(cultivar_name=data)
        if not queryset.exists():
            raise serializers.ValidationError(f'Cultivar name \'{data}\' does not exist or not approved.')
        else:
            return queryset.latest('create_time')

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset =queryset.filter(status='approved')
        return queryset


class CustomInventorySerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    cultivar_name = CustomInventoryCultivarNameField(source='cultivar')
    item_image_urls = serializers.SerializerMethodField()
    labtest_url = serializers.SerializerMethodField()

    category_required_fields = {
        'Flowers':      ('batch_availability_date', 'harvest_date', 'grade_estimate',),
        'Trims':        ('batch_availability_date', 'harvest_date',),
        'Concentrates': ('batch_availability_date', 'total_batch_quantity', 'manufacturing_date',),
        'Isolates':     ('batch_availability_date', 'total_batch_quantity', 'manufacturing_date',),
        'Terpenes':     ('batch_availability_date', 'total_batch_quantity', 'manufacturing_date',),
        'Clones':       ('rooting_days',),
    }


    def get_item_image_urls(self, obj):
        """
        Return s3 item image.
        """
        image_urls = list()
        try:
            documents = obj.extra_documents.filter(doc_type='item_image')
            for document in documents:
                if document.box_url:
                    image_urls.append(document.box_url)
                else:
                    path = document.path
                    url = create_presigned_url(AWS_BUCKET, path)
                    if url.get('response'):
                        image_urls.append(url.get('response'))
        except Exception:
            pass
        return image_urls

    def get_labtest_url(self, obj):
        """
        Return s3 labtest url.
        """
        try:
            document = obj.extra_documents.filter(doc_type='labtest').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def validate(self, attrs):
        attrs = super().validate(attrs)
        errors = dict()
        category_name = attrs.get('category_name', '')
        if not category_name:
            required_fields = ('category_name',)
        else:
            required_fields = self.category_required_fields.get(CG.get(category_name), ())
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = f'This field is required for category \'{category_name}\'.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def validate_vendor_name(self, val):
        queryset = filterQuerySet.for_user(LicenseProfile.objects.all(), self.context['request'].user)
        if not queryset.filter(name=val).exists():
            raise serializers.ValidationError(
                f'Vendor name \'{val}\' does not exist or you do not have access to vendor profile.')
        return val

    class Meta:
        model = CustomInventory
        exclude = ('cultivar', 'zoho_item_id', 'zoho_organization')
        read_only_fields = ('status', 'sku', 'created_by', 'created_on', 'updated_on', 'approved_by', 'approved_on',)


class  InventoryItemEditSerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """

    class Meta:
        model = InventoryItemEdit
        exclude = ()
        read_only_fields = ('status', 'created_by', 'created_on', 'updated_on', 'approved_by', 'approved_on',)

class  InventoryItemQuantityAdditionSerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """

    class Meta:
        model = InventoryItemQuantityAddition
        exclude = ()
        read_only_fields = ('status', 'created_by', 'created_on', 'updated_on', 'approved_by', 'approved_on',)

class  InventoryItemDelistSerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """

    class Meta:
        model = InventoryItemDelist
        exclude = ('item_data',)
        read_only_fields = (
            'name',
            'status',
            'sku',
            'zoho_item_id',
            'cultivar_name',
            'vendor_name',
            'approved_by',
            'approved_on',
            'created_by',
            'created_on',
            'updated_on',
        )

