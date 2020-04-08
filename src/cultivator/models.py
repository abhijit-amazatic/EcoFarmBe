"""
cultivator(is also known as Vendor) related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
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
        _('Uploaded Sellers Permit TO'), blank=True, null=True, max_length=255)

    def __str__(self):
        return self.legal_business_name
    
    

    
    
    
