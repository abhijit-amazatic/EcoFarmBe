from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField, HStoreField,)

from reversion.models import Revision


class ReversionMeta(models.Model):
    revision = models.OneToOneField('reversion.Revision', related_name='reversion_meta', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(_('IP address'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True, null=True)
    origin = models.CharField(_('Origin'), max_length=255, blank=True, null=True)
    path = models.CharField(_('Path'), max_length=255, blank=True, null=True)
    deleted_objects = JSONField(_('Deleted Objects'), null=True, blank=True, default=list)
    created_objects = JSONField(_('Created Objects'), null=True, blank=True, default=list)

class OldVersion(models.Model):
    version = models.OneToOneField('reversion.Version', related_name='old_version', on_delete=models.CASCADE)
    format = models.CharField(
        max_length=255,
        help_text="The serialization format used by this model.",
    )
    serialized_data = models.TextField(
        help_text="The serialized form of prev instance of the model.",
    )
