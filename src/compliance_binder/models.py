"""
Brand related schemas defined here.
"""
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



class BinderLicense(TimeStampFlagModelMixin,StatusFlagMixin, models.Model):
    """
    Stores License Profile for either related to brand or individual user-so category & buyer and seller.
    """
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
    # is_buyer = models.BooleanField(_('Is Buyer/accounts(if individual user)'), default=False)
    # is_seller = models.BooleanField(_('Is Seller/Vendor(if individual user)'), default=False)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    zoho_books_id = models.CharField(_('Zoho Books ID'), max_length=100, blank=True, null=True)
    status_before_expiry = models.CharField(_('License status before expiry'), max_length=100, blank=True, null=True)
    documents = GenericRelation(Documents)

    def __str__(self):
        return self.legal_business_name

    class Meta:
        verbose_name = _('License')
