"""
Serializers to related permission modules.
"""

from rest_framework import serializers
from .models import (
    Permission,
)


class PermissionSerializer(serializers.ModelSerializer):
    """
    This defines organization role serializer.
    """
    # display_name = serializers.CharField(
    #     source='get_codename_display'
    # )
    class Meta:
        model = Permission
        fields = ('id', 'name',)
