"""
Serializer for inventory
"""
from rest_framework import serializers
from .models import (Cultivar, )

class CultivarSerializer(serializers.ModelSerializer):
    """
    Cultivar Serializer
    """
    class Meta:
        model = Cultivar
        fields = ('__all__')