"""
Accounts related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField,JSONField,HStoreField,)
from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, )
from django.conf import settings
from user.models import User


class Account(StatusFlagMixin,models.Model):
    """
    Stores accounts initial details.(STEP1)
    """
    CATEGORY_CULTIVATOR = 'cultivator'
    CATEGORY_DISTRIBUTOR = 'distributor'
    CATEGORY_MANUFACTURER = 'manufacturer'
    CATEGORY_RETAILER = 'retailer'
    CATEGORY_CHOICES = (
        (CATEGORY_CULTIVATOR, _('Cultivator')),
        (CATEGORY_DISTRIBUTOR, _('Distributor')),
        (CATEGORY_MANUFACTURER, _('Manufacturer')),
        (CATEGORY_RETAILER, _('Retailer')),
    )
    account_name = models.CharField(
        _('Account Name'), blank=True, null=True, max_length=255)
    ac_manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Account Manager'),
                                   related_name='manages_accounts', null=True, blank=True, default=None, on_delete=models.CASCADE)
    account_category = models.CharField(verbose_name=_('Account Category'),max_length=60, choices=CATEGORY_CHOICES)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    approved_on = models.DateTimeField(_('Approved on'), blank=True, null=True)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    is_updated_in_crm = models.BooleanField(_('Is Updated In CRM'), default=False)
    zoho_crm_id = models.CharField(_('Zoho CRM ID'), max_length=100, blank=True, null=True)
    profile_type = ArrayField(models.CharField(
        max_length=255, blank=True),blank=True, null=True, default=list)
    number_of_licenses = models.IntegerField(null=True)
    number_of_legal_entities = models.IntegerField(null=True)

    def __str__(self):
        return self.account_category

    class Meta:
        verbose_name = _('Account',)
        #unique_together = (('ac_manager', 'account_category'), )

class AccountUser(models.Model):
    """
    Stores account's User's details.
    """
    ROLE_OWNER = 'owner'
    ROLE_LICENSE_OWNER = 'license_owner'
    ROLE_LOGISTICS = 'logistics'
    ROLE_SALES_OR_INVENTORY = 'sales_or_inventory'
    ROLE_CHOICES = (
        (ROLE_OWNER, _('Owner')),
        (ROLE_LICENSE_OWNER, _('License Owner')),
        (ROLE_LOGISTICS, _('Logistics')),
        (ROLE_SALES_OR_INVENTORY, _('Sales or Inventory')),
    )
    account = models.ForeignKey(Account, verbose_name=_('Account'),
                             related_name='account_roles', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'),
                             related_name='account_user_roles', on_delete=models.CASCADE)
    role = models.CharField(
        verbose_name=_('Role'),
        max_length=60, choices=ROLE_CHOICES
    )
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    
    class Meta:
        unique_together = (('account', 'user'), )


class AccountLicense(models.Model):
    """
    Stores account's License details.(STEP1)
    """
    account = models.ForeignKey(
        Account,
        related_name='account_license',
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
    is_draft = models.BooleanField(_('Is Draft'), default=False)



class AccountBasicProfile(models.Model):
    """
    Stores account's License details.(STEP2)
    """
    account = models.OneToOneField(
        Account,
        related_name='account_profile',
        on_delete=models.CASCADE,
    )
    company_name = models.CharField(
        _('Company Name'), blank=True, null=True, max_length=255)
    about_company = models.TextField(null=True, blank=True) 
    region = models.CharField(
        _('Region'), blank=True, null=True, max_length=255)
    preferred_payment = models.CharField(
        _('Preferred Payment'), blank=True, null=True, max_length=255)
    cultivars_of_interest = ArrayField(models.CharField(
        max_length=255, blank=True),blank=True, null=True)
    ethics_and_certification = ArrayField(models.CharField(
        max_length=255, blank=True),blank=True, null=True)
    product_of_interest = ArrayField(models.CharField(
        max_length=255, blank=True),blank=True, null=True)
    provide_transport = models.CharField(
        _('Provide Transport'), blank=True, null=True, max_length=255)
    is_draft = models.BooleanField(_('Is Draft'), default=False)



class AccountContactInfo(models.Model):
    """
    Stores account's Contacts details.(STEP3)
    """
    account = models.OneToOneField(
        Account,
        related_name='account_contact',
        on_delete=models.CASCADE,
    )
    company_phone = models.CharField(
        _('Company Phone'), blank=True, null=True, max_length=255)
    website = models.CharField(
        _('Website'), blank=True, null=True, max_length=255)
    company_email = models.CharField(
        _('Compony Email'), blank=True, null=True, max_length=255)
    employees = ArrayField(HStoreField(default=dict, ), default=list)
    instagram = models.CharField(
        _('Instagram'), blank=True, null=True, max_length=255)
    linked_in = models.CharField(
        _('Linked In'), blank=True, null=True, max_length=255)
    twitter = models.CharField(
        _('Twitter'), blank=True, null=True, max_length=255)
    facebook = models.CharField(
        _('facebook'), blank=True, null=True, max_length=255)
    # Billing and Mailing Addresses
    billing_address = JSONField(null=True, blank=True, default=dict)
    mailing_address = JSONField(null=True, blank=True, default=dict)
    is_draft = models.BooleanField(_('Is Draft'), default=False)

