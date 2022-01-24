"""
Integration serializer
"""
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from brand.models import (
    License,
    ProfileCategory,
)
from fee_variable.models import (
    Program,
    ProgramProfileCategoryAgreement,
)
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
    premises_address = serializers.CharField(max_length=255)
    premises_state = serializers.CharField(max_length=255)
    premises_city = serializers.CharField(max_length=255)
    premises_zip = serializers.CharField(max_length=255)


    def validate(self, attrs):
        prefill_tags = {
            "license_number": attrs['license_number'],
            "company": attrs['legal_business_name'],
            "full_name": attrs['license_owner_name'],
            "email": attrs['license_owner_email'],
            "address": (
                f"{attrs['premises_address']}, "
                f"{attrs['premises_city']}, "
                f"{attrs['premises_state']} - {attrs['premises_zip']}"
            ),
        }
        return prefill_tags


class W9SignPrefillDataSerializer(serializers.Serializer):
    """
    W9 Sign (using Box Sign) request prefill data Serializer
    """
    BUSSINESS_STRUCTURE_CHOICES_TAGS = {
        'Individual': 'bs_individual',
        'C Corporation': 'bs_c_corporation',
        'S Corporation': 'bs_s_corporation',
        'Partnership': 'bs_partnership',
        'Trust': 'bs_trust',
        'LLC': 'bs_llc',
        'Other': 'bs_other',
    }
    license_owner_name = serializers.CharField(max_length=255)
    legal_business_name = serializers.CharField(max_length=255)
    premises_address = serializers.CharField(max_length=255)
    premises_city = serializers.CharField(max_length=255)
    premises_state = serializers.CharField(max_length=255)
    premises_zip = serializers.CharField(max_length=255)
    bussiness_structure = serializers.ChoiceField(choices=list(BUSSINESS_STRUCTURE_CHOICES_TAGS.keys()))
    ssn = serializers.CharField(required=False, min_length=9, max_length=11)
    ein = serializers.CharField(required=False, min_length=9, max_length=10)


    def validate_ssn(self, value):
        ssn = list(value.replace('-', '').replace(' ', ''))
        middle_space = 4 * ' '
        return ' '.join(ssn[:3]) + middle_space + ' '.join(ssn[3:5]) + middle_space + ' '.join(ssn[5:])

    def validate_ein(self, value):
        ein = list(value.replace('-', '').replace(' ', ''))
        middle_space = 4 * ' '
        return ' '.join(ein[:2]) + middle_space + ' '.join(ein[2:])

    def bussiness_structure_tags(self, value):
        tags = {}
        if value in self.BUSSINESS_STRUCTURE_CHOICES_TAGS:
            for k, v in self.BUSSINESS_STRUCTURE_CHOICES_TAGS.items():
                if value == k:
                    tags[v] = True
                else:
                    tags[v] = False
        return tags

    def validate(self, attrs):
        if not attrs.get('ssn') and not attrs.get('ein'):
            raise ValidationError("At leas one field out of \'ssn\' and \'ein\' is required.")

        prefill_tags = {
            "full_name": attrs['license_owner_name'],
            "company": attrs['legal_business_name'],
            "premises_address": attrs['premises_address'],
            "city_state_zip": (
                f"{attrs['premises_city']}, "
                f"{attrs['premises_state']}, "
                f"{attrs['premises_zip']}"
            ),
            "ssn": attrs['ssn'],
            "ein": attrs['ein'],
        }
        prefill_tags.update(self.bussiness_structure_tags(attrs['bussiness_structure']))
        return prefill_tags


class BoxSignRecipientSerializer(serializers.Serializer):
    """
    Box Sign request Recipient Serializer
    """
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(max_length=255)


class BoxSignRelatedProgramNameField(serializers.RelatedField):
    queryset = Program.objects.get_queryset()

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
        "w9": W9SignPrefillDataSerializer,
    }

    # license = serializers.PrimaryKeyRelatedField(queryset=License.objects)
    recipient = BoxSignRecipientSerializer(write_only=True)
    source_file_id = serializers.CharField(write_only=True, required=False, max_length=255)
    # doc_type = serializers.CharField(max_length=255)
    # doc_type = serializers.ChoiceField(choices=BoxSignDocType.DOC_TYPE_CHOICES)
    # doc_type = serializers.RelatedField(queryset=BoxSignDocType.objects)
    program_name = BoxSignRelatedProgramNameField(required=False)
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
        else:
            attrs = self.validate_doc_type_other(attrs)

        if hasattr(self, f"get_prefill_tags_{doc_type}"):
            attrs['prefill_tags'] = getattr(self, f"get_prefill_tags_{doc_type}")(attrs)
        else:
            attrs['prefill_tags'] = {**attrs['prefill_data']}

        return attrs

    def validate_doc_type_agreement(self, attrs):
        default_program = None
        profile_category = attrs['license'].profile_category or ''
        if not attrs.get('program_name'):
            try:
                qs = ProfileCategory.objects.select_related('default_program')
                profile_category_obj = qs.get(name=profile_category)
            except ObjectDoesNotExist:
                pass
            else:
                if profile_category_obj.default_program:
                    attrs['program_name'] = default_program = profile_category_obj.default_program

        if attrs['program_name']:
            try:
                qs = ProgramProfileCategoryAgreement.objects.get_queryset()
                qs = qs.select_related('agreement')
                program_profile_category_agreement_obj = qs.get(
                    program=attrs['program_name'],
                    profile_category__name=profile_category,
                )
            except ObjectDoesNotExist:
                if not default_program:
                    raise ValidationError({
                        "program_name": (
                            f"This program is not added to profile category '{profile_category}')"
                        )
                    })
                else:
                    attrs['program_name'] = None
            else:
                attrs.setdefault(
                    'source_file_id', program_profile_category_agreement_obj.agreement.box_source_file_id
                )


        if not attrs.get('program_name'):
            raise ValidationError({
                "program_name": (
                    "This field is required.(Default program_name not found "
                    f"for profile_category \'{profile_category}\')"
                )
            })

        if not attrs['source_file_id']:
            raise ValidationError({"source_file_id": "This field is required."})

        attrs['program_name'] = attrs['program_name'].name
        return attrs

    def validate_doc_type_w9(self, attrs):
        if settings.BOX_SIGN_W9_TEMPLATE_ID:
            attrs['source_file_id'] = settings.BOX_SIGN_W9_TEMPLATE_ID
        return self.validate_doc_type_other(attrs)

    def validate_doc_type_other(self, attrs):
        if not attrs.get('source_file_id'):
            raise ValidationError({"source_file_id": "This field is required for current doc_type."})
        return attrs


    class Meta:
        model = BoxSign
        # fields = ('__all__')
        exclude = (
            'id',
            'fields',
            # 'response',
        )
        read_only_fields = (
            'request_id',
            'status',
            'signer_decision',
            'output_file_id',
            'signer_embed_url',
            'fields',
        )
