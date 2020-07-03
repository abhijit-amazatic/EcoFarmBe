"""
Serializer for inventory
"""
from rest_framework import serializers
from .models import (Inventory, )
from labtest.models import (LabTest, )
from labtest.serializers import (LabTestSerializer, )

class InventorySerializer(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    class Meta:
        model = Inventory
        depth = 1
        exclude = ()

class InventoryDetailSerializer(InventorySerializer):
    """
    Inventory Details Serializer
    """
    labtest = serializers.SerializerMethodField()
    
    def get_labtest(self, obj):
        try:
            labtest = LabTest.objects.get(Inventory_SKU=obj.sku)
            labtest = LabTestSerializer(labtest)
            return labtest.data
        except LabTest.DoesNotExist:
            return None
        
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