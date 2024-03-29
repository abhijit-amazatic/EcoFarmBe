"""
Fees related serializers defined here.
Basically they are used for API representation & validation.
"""
import re
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from integration.box import get_embed_url
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

    class Meta:
        model = CustomInventoryVariable
        fields = ('__all__')


class TaxVariableVariableSerializer(serializers.ModelSerializer):
    """
    This defines TaxVariableVariableSerializer
    """
    cultivar_tax = serializers.CharField(source='dried_flower_tax')
    trim_tax = serializers.CharField(source='dried_leaf_tax')
    cultivar_tax_item = serializers.CharField(source='dried_flower_tax_item')
    trim_tax_item = serializers.CharField(source='dried_leaf_tax_item')

    class Meta:
        model = TaxVariable
        fields = ('__all__')


class AgreementSerializer(serializers.ModelSerializer):
    """
    This defines CustomInventoryVariableVariableSerializer
    """

    class Meta:
        model = Agreement
        # fields = ('__all__')
        exclude = ('id', 'created_on', 'updated_on')

class ProgramSerializer(serializers.ModelSerializer):
    """
    This defines CustomInventoryVariableVariableSerializer
    """
    agreement = AgreementSerializer()

    class Meta:
        model = Program
        fields = ('__all__')

class FileLinkSerializer(serializers.ModelSerializer):
    """
    This defines FileLinkSerializer
    """
    box_embed_url = serializers.SerializerMethodField()

    def get_box_embed_url(self, obj):
        embed_link = None
        matched = None
        if obj.url:
            box_shared_link_regex = r'^https://(?:(?P<customr_domain>[^.?=\/]*)\.)?app\.box\.com/s/(?P<shared_value>[^?\/]*)'
            matched = re.match(box_shared_link_regex, obj.url)
        if matched:
            return f"https://app.box.com/embed/s/{matched.group('shared_value')}"
        elif obj.box_file_id:
            try:
                embed_link = get_embed_url(obj.box_file_id)
            except Exception:
                pass
        return embed_link

    class Meta:
        model = FileLink
        exclude = ('id', 'created_on', 'updated_on')

