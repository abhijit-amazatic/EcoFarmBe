"""
Brand related schemas defined here.
"""
import re
import traceback
from base64 import (urlsafe_b64encode, urlsafe_b64decode)

from django.db import models
from django.db.models.deletion import SET_NULL
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField, HStoreField,)
from django.contrib.contenttypes.fields import (GenericRelation, )
from django.conf import settings
from django.utils import timezone

from cryptography.fernet import (Fernet, InvalidToken)

from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin, )
from inventory.models import (Documents, )



class BinderLicense(TimeStampFlagModelMixin, models.Model):
    """
    Stores License Profile for either related to brand or individual user-so category & buyer and seller.
    """
    STATUS_CHOICES = (
        ('Active', _('Active')),
        ('Cancelled', _('Cancelled')),
        ('About to Expire', _('About to Expire')),
        ('Expired', _('Expired')),
        ('Expired - Pending Renewal', _('Expired - Pending Renewal')),
        ('Inactive', _('Inactive')),
        ('Revoked', _('Revoked')),
        ('Surrendered', _('Surrendered')),
        ('Suspended', _('Suspended')),
    )

    profile_license = models.OneToOneField('brand.License', verbose_name=_('Profile License'), blank=True, null=True, on_delete=SET_NULL,)

    license_number = models.CharField(_('License Number'), max_length=255)
    legal_business_name = models.CharField(_('Legal Business Name'), max_length=255)
    license_type = models.CharField(_('License Type'), blank=True, null=True, max_length=255)
    profile_category = models.CharField(_('Profile Category'), blank=True, null=True, max_length=255)
    premises_address = models.TextField(blank=True, null=True)
    premises_county = models.CharField(_('Premises County'), blank=True, null=True, max_length=255)
    premises_city = models.CharField(_('Premises City'), blank=True, null=True, max_length=255)
    premises_apn = models.CharField(_('Premises APN'), blank=True, null=True, max_length=255)
    premises_state = models.CharField(_('Premises State'), blank=True, null=True, max_length=255)
    zip_code = models.CharField(_('Premises Zip'), blank=True, null=True, max_length=255)
    issue_date = models.DateField(_('Issue Date'), blank=True, null=True, default=None)
    expiration_date = models.DateField(_('Expiration Date'), blank=True, null=True, default=None)
    uploaded_license_to = models.CharField(_('Uploaded To'), blank=True, null=True, max_length=255)
    uploaded_sellers_permit_to = models.CharField(_('Uploaded Sellers Permit To'), blank=True, null=True, max_length=255)
    uploaded_w9_to = models.CharField(_('Uploaded W9  To'), blank=True, null=True, max_length=255)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    is_updated_via_trigger = models.BooleanField(_('Is Updated Via Trigger'), default=False)

    license_status = models.CharField(choices=STATUS_CHOICES, blank=True, null=True, max_length=255,)

    documents = GenericRelation(Documents)

    @property
    def status(self):
        if self.license_status:
            return self.license_status
        elif self.expiration_date:
            if self.expiration_date >= timezone.now().date():
                return 'Active'
            else:
                return 'Expired'
        else:
            return ''

    def __str__(self):
        return self.legal_business_name

    class Meta:
        verbose_name = _('License')
