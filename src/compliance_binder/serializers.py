"""
Serializer to validate brand related modules.
"""

from typing import OrderedDict
import requests
from tempfile import TemporaryFile

from django.db import models
from django.conf import settings
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from core.settings import (AWS_BUCKET, )
from user.models import User
from inventory.models import (Documents, )
from core.utility import (email_admins_on_profile_registration_completed,notify_admins_on_slack_complete,)
from inventory.models import (Documents, )
from integration.box import upload_file
from integration.apps.aws import (create_presigned_url, )
from user.models import (User,)
from utils import (reverse_admin_change_path,)
from .models import (
    BinderLicense,
)


class ListGroupBySerializer(serializers.ListSerializer):
    group_by_field = 'profile_category'

    def to_representation(self, data):
        if isinstance(data, models.Manager):
            data = data.all()
        if isinstance(data, models.QuerySet):
            resp_data = {
                cat: super(ListGroupBySerializer, self).to_representation(data.filter(profile_category=cat))
                for cat in data.values_list(self.group_by_field, flat=True).distinct()
            }
        else:
            cat_list = list(set(x.profile_category for x in data))
            resp_data = {
                cat: super(ListGroupBySerializer, self).to_representation(
                    [x for x in data if getattr(x, self.group_by_field, '') == cat]
                )
                for cat in cat_list
            }
        return resp_data

    @property
    def data(self):
        return super(serializers.ListSerializer, self).data


class BinderLicenseSerializer(serializers.ModelSerializer):
    """
    This defines license serializer.
    """
    status=serializers.ReadOnlyField()
    license_url = serializers.SerializerMethodField()
    seller_permit_url = serializers.SerializerMethodField()
    license_profile_url = serializers.SerializerMethodField()

    def get_license_profile_url(self, obj):
        """
        Return s3 license url.
        """
        if obj.profile_license:
            try:
                document = Documents.objects.filter(object_id=obj.profile_license.id, doc_type='profile_image').latest('created_on')
                if document.box_url:
                    return document.box_url
                else:
                    path = document.path
                    url = create_presigned_url(AWS_BUCKET, path)
                    if url.get('response'):
                        return url.get('response')
            except Exception:
                pass
        return None
    
    def get_license_url(self, obj):
        """
        Return s3 license url.
        """
        if obj.profile_license:
            try:
                license = Documents.objects.filter(object_id=obj.profile_license.id, doc_type='license').latest('created_on')
                if license.box_url:
                    return license.box_url
                else:
                    path = license.path
                    url = create_presigned_url(AWS_BUCKET, path)
                    if url.get('response'):
                        return url.get('response')
            except Exception:
                pass
        return None

    def get_seller_permit_url(self, obj):
        """
        Return s3 license url.
        """
        if obj.profile_license:
            try:
                seller = Documents.objects.filter(object_id=obj.profile_license.id, doc_type='seller_permit').latest('created_on')
                if seller.box_url:
                    return seller.box_url
                else:
                    path = seller.path
                    url = create_presigned_url(AWS_BUCKET, path)
                    if url.get('response'):
                        return url.get('response')
            except Exception:
                pass
        return None


    class Meta:
        model = BinderLicense
        fields = ('__all__')
        list_serializer_class = ListGroupBySerializer
        # read_only_fields = ('status', 'created_on', 'updated_on')
        # exclude = ('profile_category', )
