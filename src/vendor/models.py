"""
cultivator(is also known as Vendor) related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from core.validators import full_domain_validator
from django.conf import settings
from user.models import User


class Vendor(models.Model):
    """
    Stores vendor's/cultivator's initial details.
    """    
    ac_manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Account Manager'),
                                   related_name='manages', null=True, blank=True, default=None, on_delete=models.CASCADE)
    vendor_categories = models.ManyToManyField(
        to='VendorCategory',
        related_name='vendor_category',
        blank=False,
    )
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


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

    
class VendorUser(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. User's details.
    """
    ROLE_OWNER = 'OWNER'
    ROLE_USER = 'USER'
    ROLE_CHOICES = (
        (ROLE_OWNER, _('Owner')),
        (ROLE_USER, _('User')),
    )
    vendor = models.ForeignKey(Vendor, verbose_name=_('Vendor'),
                             related_name='vendor_roles', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'),
                             related_name='user_roles', on_delete=models.CASCADE)
    role = models.CharField(verbose_name=_('Role'),max_length=8, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = (('vendor', 'user'), )


class VendorProfile(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. Farm profile details.
    """
    vendor = models.ForeignKey(Vendor, verbose_name=_('Vendor'),
                                related_name='vendor_profile', on_delete=models.CASCADE)
    profile_type = ArrayField(models.CharField(
        max_length=255, blank=True),blank=True, null=True)
    number_of_licenses = models.IntegerField(null=True)
    number_of_legal_entities = models.IntegerField(null=True)


class ProfileContact(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='profile_contact', on_delete=models.CASCADE)
    profile_contact_details = JSONField(null=True, blank=True, default=dict)
    
        
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
    premises_country = models.CharField(
        _('Premises Country'), blank=True, null=True, max_length=255)
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

    def __str__(self):
        return self.legal_business_name


class ProfileOverview(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's  overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='cultivation_overview', on_delete=models.CASCADE)
    profile_overview = JSONField(null=True, blank=True, default=dict)
    
    
class FinancialOverview(models.Model):
    """
    Stores vendor's/cultivator's/Nursary's/etc. farm's Financial overview.
    """
    vendor_profile = models.OneToOneField(VendorProfile, verbose_name=_('VendorProfile'),
                                related_name='financial_overview', on_delete=models.CASCADE)
    financial_details = JSONField(null=True, blank=True, default=dict)
    
    
    
    
    
