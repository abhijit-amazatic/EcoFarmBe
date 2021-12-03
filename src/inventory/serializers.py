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
from fee_variable.utils import get_item_mcsp_fee
from .utils import get_item_tax
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


class BaseInventorySerializer(serializers.ModelSerializer):
    """
    Base Inventory Serializer
    """
    mobile_url = serializers.SerializerMethodField(method_name='tile_image_patch')

    def tile_image_patch(self, obj):
        url = obj.mobile_url
        if not url:
            for d in obj.extra_documents.all():
                if d.S3_mobile_url or d.S3_url:
                    url = d.S3_mobile_url or d.S3_url
                    break
        return url

    class Meta:
        model = Inventory
        read_only_fields = ('mobile_url',)
        depth = 1


class InventorySerializer(BaseInventorySerializer):
    """
    Inventory Serializer
    """
    class Meta(BaseInventorySerializer.Meta):
        exclude = ()


class LogoutInventorySerializer(BaseInventorySerializer):
    """
    Logout serializer.
    """
    class Meta(BaseInventorySerializer.Meta):
        fields = (
            'created_time',
            'item_id',
            'name',
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
            'mobile_url',
            'parent_category_name',
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
    profile_id = serializers.IntegerField(required=True)
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
        if data:
            queryset = self.get_queryset()
            queryset = queryset.filter(cultivar_name=data)
            if not queryset.exists():
                raise serializers.ValidationError(f'Cultivar name \'{data}\' does not exist or not approved.')
            else:
                return queryset.latest('create_time')
        else:
            return None

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset =queryset.filter(status='approved')
        return queryset


class CustomInventorySerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    cultivar_name = CustomInventoryCultivarNameField(source='cultivar', required=False, allow_null=True, allow_empty=True)
    item_image_urls = serializers.SerializerMethodField()
    labtest_url = serializers.SerializerMethodField()
    # license_profile = serializers.PrimaryKeyRelatedField(
    #     queryset=LicenseProfile.objects.get_queryset(),
    #     required=True,
    #     allow_null=False,
    # )
    required_fields = ('license_profile',)
    category_required_fields = {
        # 'Flowers':      ('mcsp_fee', 'cultivation_tax', 'cultivar_name', 'batch_availability_date', 'harvest_date', 'grade_estimate',),
        'Flowers':      ('mcsp_fee', 'cultivar_name', 'batch_availability_date', 'harvest_date', 'grade_estimate',),
        'Trims':        ('mcsp_fee', 'cultivar_name', 'batch_availability_date', 'harvest_date',),
        'Kief':         ('mcsp_fee', 'cultivar_name', 'batch_availability_date', 'manufacturing_date',),
        'Concentrates': ('mcsp_fee', 'cultivar_name', 'batch_availability_date', 'manufacturing_date', 'biomass_type',),
        'Distillates':  ('mcsp_fee', 'mfg_batch_id',  'batch_availability_date', 'manufacturing_date', 'biomass_type', 'cannabinoid_percentage',),
        'Isolates':     ('mcsp_fee', 'mfg_batch_id',  'batch_availability_date', 'manufacturing_date', 'biomass_type', 'cannabinoid_percentage',),
        'Terpenes':     ('mcsp_fee', 'cultivar_name', 'batch_availability_date', 'manufacturing_date', ),
        'Clones':       ('mcsp_fee', 'cultivar_name', 'rooting_days',),
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

        for field in self.required_fields:
            if not attrs.get(field):
                errors[field] = "This field is required."

        category_name = attrs.get('category_name', '')
        cat_required_fields = self.category_required_fields.get(CG.get(category_name), ())
        for field in cat_required_fields:
            if field == 'cultivar_name':
                if attrs.get('cultivar'):
                    continue
            elif field == 'grade_estimate':
                if attrs.get('marketplace_status') in ('Vegging', 'Flowering'):
                    continue
            if attrs.get(field):
                continue
            errors[field] = f'This field is required for category \'{category_name}\'.'

        biomass_type = attrs.get('biomass_type') or ''
        if 'biomass_type' in cat_required_fields and  biomass_type in ('Dried Flower', 'Dried Leaf', 'Fresh Plant'):
            for field in ('biomass_input_g', 'total_batch_quantity'):
                if attrs.get(field):
                    continue
                errors[field] = f'This field is required for category \'{category_name}\' and  biomass type \'{biomass_type}\'.'

        if errors:
            raise serializers.ValidationError(errors)

        # if 'biomass_type' in cat_required_fields and  biomass_type in ('Dried Flower', 'Dried Leaf', 'Fresh Plant'):
        #     tax = get_item_tax(
        #         category_name=attrs.get('category_name'),
        #         biomass_type=attrs.get('biomass_type'),
        #         biomass_input_g=attrs.get('biomass_input_g'),
        #         total_batch_output=attrs.get('total_batch_quantity'),
        #     )
        #     if not attrs.get('cultivation_tax') == tax:
        #         errors['cultivation_tax'] = f'Value do not match with backend calculations (backend value: \'{tax}\').'

        # mcsp_fee = get_item_mcsp_fee(
        #     vendor_name=attrs.get('vendor_name'),
        #     license_profile=attrs.get('license_profile'),
        #     item_category=attrs.get('category_name'),
        #     farm_price=attrs.get('farm_ask_price'),
        #     no_tier_fee=True,
        # )
        # if not attrs.get('mcsp_fee') == mcsp_fee:
        #     errors['mcsp_fee'] = f'Value do not match with backend calculations (backend value: \'{mcsp_fee}\').'

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

