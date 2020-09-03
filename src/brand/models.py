"""
Brand related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin, )
from django.conf import settings
from user.models import User

class Brand(TimeStampFlagModelMixin,models.Model):
    """
    Stores Brand's details.
    """
    brand_name = models.CharField(_('Brand Name'), blank=True, null=True, max_length=255)
    ac_manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Account Manager'),
                                   related_name='manages', null=True, blank=True, default=None, on_delete=models.CASCADE)
    brand_category = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    brand_county = models.CharField(
        _('Brand County'), blank=True, null=True, max_length=255)
    appellation = models.CharField(_('Brand Appellation'), blank=True, null=True, max_length=255)
    ethics_and_certification = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    about_brand = models.TextField(blank=True, null=True)
    interested_in_cobranding = models.BooleanField(_('Is Interested In Co-Branding'), default=False)
    have_marketing = models.BooleanField(_('Have marketing'), default=False)    
    featured_on_our_site = models.BooleanField(_('Interested In Featured on Our Site'), default=False)
    is_buyer = models.BooleanField(_('Is Buyer/accounts'), default=False)    
    is_seller = models.BooleanField(_('Is Seller/Vendor'), default=False)    

    def __str__(self):
        return self.brand_name

    class Meta:
        #unique_together = (('ac_manager', 'brand_name'),)


class LicenseProfile(TimeStampFlagModelMixin, models.Model):
    """
    Stores License Profile for either related to brand or individual user.
    """
    brand = models.ForeignKey(Brand, verbose_name=_('Brand'), on_delete=models.CASCADE, blank=True, null=True)
    individual_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Individual User'),null=True, blank=True, default=None, on_delete=models.CASCADE)
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
    associated_program = models.CharField(
        _('Associated_program'), blank=True, null=True, max_length=255)
    approved_on = models.DateTimeField(_('Approved on'), blank=True, null=True)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    # profile_type = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
    # is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    # zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    # code = models.CharField(_('Vendor Code For Box'), max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.legal_business_name


class LicenseProfileUser(TimeStampFlagModelMixin, models.Model):
    """
    Stores License Profile User's details #combined roles for all accounts & vendors.
    Only farm manager is extra in vendors/sellers.
    """
    ROLE_OWNER = 'owner'
    ROLE_LICENSE_OWNER = 'license_owner'
    ROLE_FARM_MANAGER = 'farm_manager'
    ROLE_LOGISTICS = 'logistics'
    ROLE_SALES_OR_INVENTORY = 'sales_or_inventory'
    ROLE_BILLING = 'billing'
    ROLE_CHOICES = (
        (ROLE_OWNER, _('Owner')),
        (ROLE_LICENSE_OWNER, _('License Owner')),
        (ROLE_FARM_MANAGER, _('Farm Manager')),
        (ROLE_LOGISTICS, _('Logistics')),
        (ROLE_SALES_OR_INVENTORY, _('Sales or Inventory')),
        (ROLE_BILLING, _('Billing')),
    )
    license_profile = models.ForeignKey(LicenseProfile, verbose_name=_('LicenseProfile'),
                             related_name='profile_roles', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'),
                             related_name='user_roles', on_delete=models.CASCADE)
    role = models.CharField(verbose_name=_('Role'),max_length=60, choices=ROLE_CHOICES)
 
    
    class Meta:
        unique_together = (('license_profile', 'user'), )
        verbose_name = _('License Profile User')    
