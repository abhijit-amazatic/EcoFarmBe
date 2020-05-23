"""
cultivator(is also known as Vendor) related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, )
from django.conf import settings
from user.models import User


class Vendor(models.Model):
    """
    Stores vendor's/cultivator's initial details.
    """
    CATEGORY_CULTIVATION = 'cultivation'
    CATEGORY_NURSARY = 'nursery'
    CATEGORY_TESTING = 'testing'
    CATEGORY_HEALTHCARE = 'healthcare'
    CATEGORY_PATIENT = 'patient'
    CATEGORY_INVESTMENT = 'investment'
    CATEGORY_ANCILLARY_SERVICES = 'ancillary services'
    CATEGORY_ANCILLARY_PRODUCTS = 'ancillary products'
    CATEGORY_HEMP = 'hemp'
    CATEGORY_BRAND = 'brand'
    CATEGORY_EVENT = 'event'
    CATEGORY_PROCESSING = 'processing'
    CATEGORY_DISTRIBUTION = 'distribution'
    CATEGORY_MANUFACTURING = 'manufacturing'
    CATEGORY_RETAIL = 'retail'
    CATEGORY_CHOICES = (
        (CATEGORY_CULTIVATION, _('Cultivation')),
        (CATEGORY_NURSARY, _('Nursery')),
        (CATEGORY_TESTING, _('Testing')),
        (CATEGORY_HEALTHCARE, _('Healthcare')),
        (CATEGORY_PATIENT, _('Patient')),
        (CATEGORY_INVESTMENT, _('Investment')),
        (CATEGORY_ANCILLARY_SERVICES, _('Ancillary Services')),
        (CATEGORY_ANCILLARY_PRODUCTS, _('Anicllary Products')),
        (CATEGORY_HEMP, _('Hemp')),
        (CATEGORY_BRAND, _('Brand')),
        (CATEGORY_EVENT, _('Event')),
        (CATEGORY_PROCESSING, _('Processing')),
        (CATEGORY_DISTRIBUTION, _('Distribution')),
        (CATEGORY_MANUFACTURING, _('Manufacturing')),
        (CATEGORY_RETAIL, _('Retail')),
    )
    ac_manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Account Manager'),
                                   related_name='manages', null=True, blank=True, default=None, on_delete=models.CASCADE)
    vendor_category = models.CharField(verbose_name=_('Vendor Category'),max_length=60, choices=CATEGORY_CHOICES)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendor_category

    def profile_name(self):
        """
        Returns farm name/s.
        """
        vp = ProfileContact.objects.select_related('vendor_profile')
        pc = vp.filter(vendor_profile__vendor_id=self.pk)
        farm_names = [i.profile_contact_details.get('farm_name','') for i in pc]
        return ",".join(farm_names) if farm_names else "N/A"

    class Meta:
        unique_together = (('ac_manager', 'vendor_category'), )
        verbose_name = _('Vendor User')


    
class VendorUser(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. User's details.
    """
    vendor = models.ForeignKey(Vendor, verbose_name=_('Vendor'),
                             related_name='vendor_roles', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'),
                             related_name='user_roles', on_delete=models.CASCADE)
    role = models.CharField(verbose_name=_('Role'),max_length=60)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    
    class Meta:
        unique_together = (('vendor', 'user'), )
        verbose_name = _('Vendor User')


class VendorProfile(StatusFlagMixin,models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. Farm profile details.
    """
    vendor = models.ForeignKey(Vendor, verbose_name=_('Vendor'),
                                related_name='vendor_profile', on_delete=models.CASCADE)
    profile_type = ArrayField(models.CharField(
        max_length=255, blank=True),blank=True, null=True, default=list)
    number_of_licenses = models.IntegerField(null=True)
    number_of_legal_entities = models.IntegerField(null=True)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    code = models.CharField(_('Vendor Code For Box'), max_length=100, blank=True, null=True)
    is_draft = models.BooleanField(_('Is Draft'), default=False)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    approved_on = models.DateTimeField(_('Approved on'), blank=True, null=True)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)

    def profile_name(self):
        """
        Returns farm name/s.
        """
        vp = ProfileContact.objects.select_related('vendor_profile')
        pc = vp.filter(vendor_profile_id=self.pk)
        farm_names = [i.profile_contact_details.get('farm_name','') for i in pc]
        return ",".join(farm_names) if farm_names else "N/A"

    def __str__(self):
        return self.vendor.vendor_category

    class Meta:
        verbose_name = _('Vendors/Profile')

class ProfileContact(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='profile_contact', on_delete=models.CASCADE)
    profile_contact_details = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)
    
        
class License(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's farm's License details.
    """
    vendor_profile = models.ForeignKey(VendorProfile, verbose_name=_('VendorProfile'), on_delete=models.CASCADE)
    license_type = models.CharField(
        _('License Type'), blank=True, null=True, max_length=255)
    owner_or_manager = models.CharField(
        _('Owner or Manager'), blank=True, null=True, max_length=12)
    legal_business_name = models.CharField(
        _('Legal Business Name'), blank=True, null=True, max_length=255)
    license_number = models.CharField(
        _('License Number'), blank=True, null=True, max_length=255)
    expiration_date = models.DateField(
        _('Expiration Date'), blank=True, null=True, default=None)
    issue_date = models.DateField(
        _('Issue Date'), blank=True, null=True, default=None)
    premises_address = models.TextField()
    premises_county = models.CharField(
        _('Premises County'), blank=True, null=True, max_length=255)
    premises_city = models.CharField(
        _('Premises City'), blank=True, null=True, max_length=255)
    zip_code = models.CharField(
        _('Premises Zip'), blank=True, null=True, max_length=255)
    premises_apn = models.CharField(
        _('Premises APN'), blank=True, null=True, max_length=255)
    premises_state = models.CharField(
        _('Premises State'), blank=True, null=True, max_length=255)
    uploaded_license_to = models.CharField(
        _('Uploaded To'), blank=True, null=True, max_length=255)
    uploaded_sellers_permit_to = models.CharField(
        _('Uploaded Sellers Permit To'), blank=True, null=True, max_length=255)
    uploaded_w9_to = models.CharField(
        _('Uploaded W9  To'), blank=True, null=True, max_length=255)
    
    def __str__(self):
        return self.legal_business_name


class ProfileOverview(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's  overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='profile_overview', on_delete=models.CASCADE)
    profile_overview = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)
    
    
class FinancialOverview(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's Financial overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='financial_overview', on_delete=models.CASCADE)
    financial_details = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)

class ProcessingOverview(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's Processing overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='processing_overview', on_delete=models.CASCADE)
    processing_config = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)

class ProgramOverview(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's Program overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='program_overview', on_delete=models.CASCADE)
    program_details = JSONField(null=False, blank=False, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)
    
       
class VendorCategory(models.Model):
    """
    Class implementing  Vendor a categories.
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Vendor Category')
        verbose_name_plural = _('Vendor Categories')
