"""
Serializer for inventory
"""
import json
from rest_framework import serializers
from .models import (Inventory, ItemFeedback, InTransitOrder)


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
        fields = (
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
            'documents')
        
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
