"""
Integration serializer
"""
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from brand.models import License
from fee_variable.models import Program
from  .models import (
    BoxSignDocType,
    BoxSign,
)

# class IntegrationSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Integration
#         fields = ('id', 'name', 'access_token', 'refresh_token', 'access_expiry', 'refresh_expiry', 'client_id', 'client_secret')



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


class BoxSignRecipientSerializer(serializers.Serializer):
    """
    Box Sign request Recipient Serializer
    """
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(max_length=255)


class BoxSignRelatedProgramNameField(serializers.RelatedField):
    queryset = Program.objects.get_queryset().select_related('agreement')

    def to_representation(self, obj):
        if isinstance(obj, models.Model):
            return obj.name
        return obj

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(name=data)
        except queryset.model.DoesNotExist:
            raise serializers.ValidationError(
            f'Program name \'{data}\' does not exist.'
        )


class BoxSignSerializer(serializers.ModelSerializer):
    """
    Box Sign request Serializer
    """
    DOC_TYPE_PREFILL_DATA_SERIALIZERS = {
        "agreement": AgreementSignPrefillDataSerializer,
    }

    # license = serializers.PrimaryKeyRelatedField(queryset=License.objects)
    recipient = BoxSignRecipientSerializer(write_only=True)
    source_file_id = serializers.CharField(write_only=True, max_length=255)
    # doc_type = serializers.CharField(max_length=255)
    # doc_type = serializers.ChoiceField(choices=BoxSignDocType.DOC_TYPE_CHOICES)
    # doc_type = serializers.RelatedField(queryset=BoxSignDocType.objects)
    program_name = BoxSignRelatedProgramNameField()
    prefill_data = serializers.JSONField(write_only=True)


    def validate(self, attrs):
        doc_type = attrs['doc_type'].name
        if doc_type in self.DOC_TYPE_PREFILL_DATA_SERIALIZERS:
            prefill_data_serializer = self.DOC_TYPE_PREFILL_DATA_SERIALIZERS[doc_type](data=attrs['prefill_data'])
            if prefill_data_serializer.is_valid(raise_exception=False):
                attrs['prefill_data'] = prefill_data_serializer.validated_data
            else:
                raise ValidationError({"prefill_data": prefill_data_serializer.errors})

        if hasattr(self, f"validate_doc_type_{doc_type}"):
            attrs = getattr(self, f"validate_doc_type_{doc_type}")(attrs)

        if hasattr(self, f"get_prefill_tags_{doc_type}"):
            attrs['prefill_tags'] = getattr(self, f"get_prefill_tags_{doc_type}")(attrs)
        else:
            attrs['prefill_tags'] = {**attrs['prefill_data']}
        return attrs

    def validate_doc_type_agreement(self, attrs):
        if not attrs.get('program_name'):
            raise ValidationError({"program_name": "This field is required."})
        if attrs['program_name'].agreement.box_source_file_id:
            attrs['source_file_id'] = attrs['program_name'].agreement.box_source_file_id
        attrs['program_name'] = attrs['program_name'].name
        return attrs

    def get_prefill_tags_agreement(self, data):
        prefill_data = data['prefill_data']
        prefill_tags = {
            "license_number": prefill_data['license_number'],
            "company": prefill_data['legal_business_name'],
            "full_name": prefill_data['legal_business_name'],
            "email": prefill_data['license_owner_email'],
            "address": ', '.join(
                [prefill_data[k]
                 for k in ('premise_address', 'premise_city', 'premise_state', 'premise_zip')]
            ),
        }
        return prefill_tags

    @staticmethod
    def bussiness_structure_tags(value):
        tags = {}
        bussiness_structure_choices = {
            'Individual': 'bs_individual',
            'C Corporation': 'bs_c_corporation',
            'S Corporation': 'bs_s_corporation',
            'Partnership': 'bs_partnership',
            'Trust': 'bs_trust',
            'LLC': 'bs_llc',
            'Other': 'bs_other',
        }
        if value in bussiness_structure_choices:
            for k, v in bussiness_structure_choices.items():
                tag = {"document_tag_id": k}
                if value == k:
                    tag[v] = True
                else:
                    tag[v] = False
                tags.append(tag)
        return tags

    class Meta:
        model = BoxSign
        # fields = ('__all__')
        exclude = ('id', 'response', 'fields')
        read_only_fields = (
            'request_id',
            'status',
            'signer_decision',
            'output_file_id',
            'signer_embed_url',
            'fields',
        )
