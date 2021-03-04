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
