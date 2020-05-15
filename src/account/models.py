"""
accounts related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, )
from django.conf import settings
from user.models import User



class Account(models.Model):
    """
    Stores accounts initial details.
    """
    CATEGORY_CULTIVATOR = 'cultivator'
    CATEGORY_DISTRIBUTOR = 'distributor'
    CATEGORY_MANUFACTURE = 'manufacture'
    CATEGORY_RETAILER = 'retailer'
    CATEGORY_CHOICES = (
        (CATEGORY_CULTIVATOR, _('Cultivator')),
        (CATEGORY_DISTRIBUTOR, _('Distributor')),
        (CATEGORY_MANUFACTURE, _('Manufacture')),
        (CATEGORY_RETAILER, _('Retailer')),
    )
    account_name = models.CharField(
        _('Account Name'), blank=True, null=True, max_length=255)
    ac_manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Account Manager'),
                                   related_name='manages_accounts', null=True, blank=True, default=None, on_delete=models.CASCADE)
    account_category = models.CharField(verbose_name=_('Vendor Category'),max_length=60, choices=CATEGORY_CHOICES)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_category

    class Meta:
        unique_together = (('ac_manager', 'account_category'), )



class License(models.Model):
    """
    Stores account's License details.
    """
    account = models.ForeignKey(
        Account,
        verbose_name=_('Account'),
        on_delete=models.CASCADE,
    )
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

    # Location
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

    #uploads
    uploaded_license_to = models.CharField(
        _('Uploaded To'), blank=True, null=True, max_length=255)
    uploaded_sellers_permit_to = models.CharField(
        _('Uploaded Sellers Permit To'), blank=True, null=True, max_length=255)
    uploaded_w9_to = models.CharField(
        _('Uploaded W9  To'), blank=True, null=True, max_length=255)

    def __str__(self):
        return self.legal_business_name


class AccountBasicProfile(models.Model):
    """
    Stores account's License details.
    """
    account = models.ForeignKey(
        Account,
        verbose_name=_('Account'),
        on_delete=models.CASCADE,
    )
    company_name = models.CharField(
        _('Company Name'), blank=True, null=True, max_length=255)
    region = models.CharField(
        _('Region'), blank=True, null=True, max_length=255)
    preferred_payment = models.CharField(
        _('Preferred Payment'), blank=True, null=True, max_length=255)
    cultivars_of_interest = models.CharField(
        _('Cultivars Of Interest'), blank=True, null=True, max_length=255)
    ethics_and_certification = models.CharField(
        _('Ethics & Certification'), blank=True, null=True, max_length=255)
    product_of_interest = models.CharField(
        _('Product Of Interest'), blank=True, null=True, max_length=255)
    provide_transport = models.CharField(
        _('Provide Transport'), blank=True, null=True, max_length=255)

    def __str__(self):
        return self.company_name


class AccountContactInfo(models.Model):
    """
    Stores account's License details.
    """
    account = models.ForeignKey(
        Account,
        verbose_name=_('Account'),
        on_delete=models.CASCADE,
    )
    company_phone = models.CharField(
        _('Company Phone'), blank=True, null=True, max_length=255)
    website = models.CharField(
        _('Website'), blank=True, null=True, max_length=255)
    compony_email = models.CharField(
        _('Compony Email'), blank=True, null=True, max_length=255)
    owner_name = models.CharField(
        _('Owner Name'), blank=True, null=True, max_length=255)
    owner_email = models.CharField(
        _('Owner Email'), blank=True, null=True, max_length=255)
    owner_phone = models.CharField(
        _('Owner Phone'), blank=True, null=True, max_length=255)
    logistic_manager_name = models.CharField(
        _('Logistic Manager Name'), blank=True, null=True, max_length=255)
    logistic_manager_email = models.CharField(
        _('Logistic Manager Email'), blank=True, null=True, max_length=255)
    logistic_manager_phone = models.CharField(
        _('Logistic Manager Phone'), blank=True, null=True, max_length=255)

    Instagram = models.CharField(
        _('Instagram'), blank=True, null=True, max_length=255)
    linked_in = models.CharField(
        _('Linked In'), blank=True, null=True, max_length=255)
    twitter = models.CharField(
        _('Twitter'), blank=True, null=True, max_length=255)
    facebook = models.CharField(
        _('facebook'), blank=True, null=True, max_length=255)

    # Billing and Mailing Addresses
    billing_compony_name = models.CharField(
        _('Billing Nompony Name'), blank=True, null=True, max_length=255)
    billing_street = models.CharField(
        _('Billing Street'), blank=True, null=True, max_length=255)
    billing_street_line_2 = models.CharField(
        _('Billing Street Line 2'), blank=True, null=True, max_length=255)
    billing_city = models.CharField(
        _('Billing City'), blank=True, null=True, max_length=255)
    billing_zip_code = models.CharField(
        _('Billing Zip Code'), blank=True, null=True, max_length=255)
    billing_state = models.CharField(
        _('Billing Zip Code'), blank=True, null=True, max_length=255)

    def __str__(self):
        return self.company_name
