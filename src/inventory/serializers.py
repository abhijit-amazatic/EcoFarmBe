"""
Serializer for inventory
"""
import json
from rest_framework import serializers
from .models import (Inventory, ItemFeedback)


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