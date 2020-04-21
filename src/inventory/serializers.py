"""
Serializer for inventory
"""
from rest_framework import serializers
from .models import (Inventory, )

class InventorySerialier(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    class Meta:
        model = Inventory
        fields = ('__all__')