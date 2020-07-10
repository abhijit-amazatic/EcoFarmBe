"""
Serializer for inventory
"""
import json
from rest_framework import serializers
from .models import (Inventory, )
from core.settings import (INVENTORY_TAXES, )

class InventorySerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    pre_tax_price = serializers.SerializerMethodField()
    
    def get_pre_tax_price(self, obj):
        """
        Get pre tax price.
        """
        if not isinstance(INVENTORY_TAXES, dict):
            taxes = json.loads(INVENTORY_TAXES)
        else:
            taxes = INVENTORY_TAXES
        if 'Flower' in obj.category_name:
            return obj.price - taxes['Flower']
        elif 'Trim' in obj.category_name:
            return obj.price - taxes['Trim']
    
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
            'cf_strain_name',
            'cf_cultivation_type',
            'cf_cannabis_grade_and_category',
            'available_stock',
            'category_name')