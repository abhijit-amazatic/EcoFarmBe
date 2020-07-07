"""
Serializer for inventory
"""
from rest_framework import serializers
from .models import (Inventory, )

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
            'cf_strain_name',
            'cf_cultivation_type',
            'cf_potency',
            'cf_cbd',
            'cf_cannabis_grade_and_category',
            'available_stock',
            'category_name')