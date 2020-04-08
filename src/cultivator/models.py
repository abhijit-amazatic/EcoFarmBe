"""
cultivator(is also known as Vendor) related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField,)
from core.validators import full_domain_validator
from django.conf import settings
from user.models import User


class Vendor(models.Model):
    """
    Stores vendor's/cultivator's initial details.
    """    
    ac_manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Account Manager'),
                                   related_name='manages', null=True, blank=True, default=None, on_delete=models.CASCADE)
    number_of_licenses = models.IntegerField(null=True)
    number_of_legal_entities = models.IntegerField(null=True)
    cultivator_categories = models.ManyToManyField(
        to='CultivatorCategory',
        related_name='cultivaotr_category',
        blank=True,
    )
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class CultivatorCategory(models.Model):
    """
    Class implementing  cultivator a categories.
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Cultivator Category')
        verbose_name_plural = _('Cultivator Categories')


class License(models.Model):
    """
    Stores vendor's/cultivator's License details.
    """
    vendor = models.ForeignKey(Vendor, verbose_name=_('Vendor'), on_delete=models.CASCADE)
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
    
    
class VendorUser(models.Model):
    """
    Stores vendor's/cultivator's User's details.
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

    
class FarmProfile(models.Model):
    """
    Stores vendor's/cultivator's Farm profile details.
    """
    vendor = models.OneToOneField(Vendor, verbose_name=_('Vendor'),
                                related_name='farm_profile', on_delete=models.CASCADE)
    name = models.CharField(_('Farm Profile'), blank=True, null=True, max_length=255)
    primary_country = models.CharField(_('Primary Country'), blank=True, null=True, max_length=60)
    appellation = models.CharField(_('Appellation'), blank=True, null=True, max_length=255)
    region = models.CharField(_('Region'), blank=True, null=True, max_length=60)
    ethics_and_certifications = ArrayField(models.CharField(
        _('Ethics & Cert'),
        choices=(('Minority Owned', 'Minority Owned'),
                 ('Locally Owned', 'Locally Owned'),
                 ('Public Benefit Corp', 'Public Benefit Corp'),
                 ('Woman', 'Woman'),
                 ('First Nation Owned', 'First Nation Owned'),
                 ('Veganic', 'Veganic'),), max_length=60,),blank=True, null=True)
    other_distributors = models.BooleanField(default=False)
    transportation = ArrayField(models.CharField(
        _('Transportation'),
        choices=(('self transport', 'Self Transport'),), max_length=16,), blank=True, null=True)
    packaged_flower_line = models.BooleanField(default=False)
    interested_in_cobranding = models.BooleanField(default=False)
    marketing_material = models.BooleanField(default=False)
    featured_on_site = models.BooleanField(default=False)
    company_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(_('Phone'), max_length=20, null=True)
    website = models.CharField(_('URL'), max_length=255, blank=False, null=False,
                           db_index=True, unique=True, validators=[full_domain_validator])
    instagram_url = models.CharField(
        _('Instagram Link'), blank=True, null=True, max_length=255)
    facebook_url = models.CharField(
        _('Facebook Link'), blank=True, null=True, max_length=255)
    linkedin_url = models.CharField(
        _('LinkedIn Link'), blank=True, null=True, max_length=255)
    twitter_url = models.CharField(
        _('Twitter Link'), blank=True, null=True, max_length=255)
    number_of_employee = models.IntegerField(null=True)
    
    
    
class CultivationOverview(models.Model):
    """
    Stores vendor's/cultivator's overview.
    """
    vendor = models.OneToOneField(Vendor, verbose_name=_('Vendor'),
                                related_name='cultivation_overview', on_delete=models.CASCADE)    
    
    
class FinancialOverview(models.Model):
    """
    Stores vendor's/cultivator's Financial overview.
    """
    vendor = models.OneToOneField(Vendor, verbose_name=_('Vendor'),
                                related_name='financial_overview', on_delete=models.CASCADE)    
    
    
    
    
    
