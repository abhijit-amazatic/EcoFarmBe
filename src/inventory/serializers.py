"""
Serializer for inventory
"""
import json
from rest_framework import serializers
from brand.permissions import filterQuerySet
from brand.models import LicenseProfile
from cultivar.models import Cultivar
from .models import (
    Inventory,
    CustomInventory,
    ItemFeedback,
    InTransitOrder,
    Documents,
)


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
                user=validated_data['user'],
                profile_id=validated_data['profile_id']
            )
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
        obj = queryset.filter(cultivar_name=data).first()
        if not obj:
            raise serializers.ValidationError(f'Cultivar name \'{data}\' does not exist or not approved.')
        else:
            return obj

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset =queryset.filter(status='approved')
        return queryset


class CustomInventorySerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    cultivar_name = CustomInventoryCultivarNameField(source='cultivar')
    item_image_url = serializers.SerializerMethodField()
    labtest_url = serializers.SerializerMethodField()

    def get_item_image_url(self, obj):
        """
        Return s3 item image.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='item_image').latest('created_on')
            if document.box_url:
                return document.box_url
            else:
                path = document.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def get_labtest_url(self, obj):
        """
        Return s3 labtest url.
        """
        try:
            document = Documents.objects.filter(object_id=obj.id, doc_type='labtest').latest('created_on')
            if license.box_url:
                return license.box_url
            else:
                path = license.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def validate_vendor_name(self, val):
        queryset = filterQuerySet.for_user(LicenseProfile.objects.all(), self.context['request'].user)
        if not queryset.filter(name=val).exists():
            raise serializers.ValidationError(
                f'Vendor name \'{val}\' does not exist or you do not have access to vendor profile.')
        return val

    class Meta:
        model = CustomInventory
        exclude = ('cultivar',)