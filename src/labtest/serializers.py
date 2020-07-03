from rest_framework import serializers
from .models import (LabTest, )

class LabTestSerializer(serializers.ModelSerializer):
    """
    LabTest Serializer
    """
    class Meta:
        model = LabTest
        fields = ('__all__')
        
