"""
Fees related serializers defined here.
Basically they are used for API representation & validation.
"""
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .models import *

class OrderVariableSerializer(serializers.ModelSerializer):
    """
    This defines OrderVariableSerializer
    """
    class Meta:
        model = OrderVariable
        fields = ('__all__')


class McspCharField(serializers.CharField):
    read_only = True

    def to_representation(self, value):
        try:
            return str(int(float(value)))
        except:
            return None

class CustomInventoryVariableSerializer(serializers.ModelSerializer):
    """
    This defines CustomInventoryVariableVariableSerializer
    """
    mcsp_fee = serializers.CharField(source='mcsp_fee_flowers', read_only=True)
    mcsp_fee_per_g = serializers.CharField(source='mcsp_fee_concentrates', read_only=True)
    mcsp_fee_per_pcs = serializers.CharField(source='mcsp_fee_clones', read_only=True)
    class Meta:
        model = CustomInventoryVariable
        fields = ('__all__')


class TaxVariableVariableSerializer(serializers.ModelSerializer):
    """
    This defines TaxVariableVariableSerializer
    """
    class Meta:
        model = TaxVariable
        fields = ('__all__')
