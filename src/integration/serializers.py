"""
Integration serializer
"""
from rest_framework import serializers

from brand.models import License
from  .models import BoxSignDocType

# class IntegrationSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Integration
#         fields = ('id', 'name', 'access_token', 'refresh_token', 'access_expiry', 'refresh_expiry', 'client_id', 'client_secret')






class BoxSignRecipientSerializer(serializers.Serializer):
    """
    Box Sign request Recipient Serializer
    """
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(max_length=255)


class BoxSignSerializer(serializers.Serializer):
    """
    Box Sign request Serializer
    """
    recipient = BoxSignRecipientSerializer()
    source_file_id = serializers.CharField(max_length=255)
    # doc_type = serializers.CharField(max_length=255)
    doc_type = serializers.ChoiceField(choices=BoxSignDocType.DOC_TYPE_CHOICES)
    # doc_type = serializers.RelatedField(queryset=BoxSignDocType.objects)
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects)
    prefill_data = serializers.JSONField()

class AgreementSignPrefillDataSerializer(serializers.Serializer):
    """
    Agreement Sign (using Box Sign) request prefill data Serializer
    """
    license_number = serializers.CharField(max_length=255)
    legal_business_name = serializers.CharField(max_length=255)
    license_owner_name = serializers.CharField(max_length=255)
    license_owner_email = serializers.EmailField(max_length=255)
    premise_address = serializers.CharField(max_length=255)
    premise_state = serializers.CharField(max_length=255)
    premise_city = serializers.CharField(max_length=255)
    premise_zip = serializers.CharField(max_length=255)

class BoxSignAgreementSerializer(BoxSignSerializer):
    """
    Agreement Box Sign request Serializer
    """
    prefill_data = AgreementSignPrefillDataSerializer()

