"""
Serializer to validate brand related modules.
"""

from typing import OrderedDict
import requests
from tempfile import TemporaryFile

from rest_framework import serializers

from .models import (
    PageMeta,
)




class PageMetaSerializer(serializers.ModelSerializer):
    """
    This defines Page Meta serializer.
    """

    class Meta:
        model = PageMeta
        fields = ('__all__')
        # read_only_fields = ('created_on', 'updated_on')
