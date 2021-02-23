"""
Integration serializer
"""
from rest_framework import serializers
from .models import OrderVariable


# class IntegrationSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Integration
#         fields = ('id', 'name', 'access_token', 'refresh_token', 'access_expiry', 'refresh_expiry', 'client_id', 'client_secret')


class OrderVariableSerializer(serializers.ModelSerializer):
    """
    This defines OrderVariableSerializer
    """
    class Meta:
        model = OrderVariable
        fields = ('__all__')
