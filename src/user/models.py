"""
User model defined here.
"""
from django.conf import settings
from django.contrib.auth.models import (AbstractUser,)
from django.contrib.postgres.fields import (JSONField,)
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, )
from integration.apps.twilio import (send_sms, verification_call)
from two_factor.abstract_models import AbstractPhoneDevice
from two_factor.utils import get_two_factor_devices


class User(StatusFlagMixin,AbstractUser):
    """
    Class implementing a custom user model.
    """
    CATEGORY_BUSINESS = 'business'
    CATEGORY_PERSONAL = 'personal'
    MEMBERSHIP_CHOICES = (
        (CATEGORY_BUSINESS, _('Business')),
        (CATEGORY_PERSONAL, _('Personal')),
    )
    email = models.EmailField(_('Email address'), unique=True)
    username = models.CharField(
        _('Username'), max_length=150, blank=True, null=True)
    first_name = models.CharField(
        _('First Name'), max_length=255, blank=True, null=True)
    last_name = models.CharField(
        _('Last Name'), max_length=255, blank=True, null=True)
    full_name = models.CharField(
        _('Full Name'), max_length=255, blank=True, null=True)
    country = models.CharField(
        _('Country'), max_length=150, blank=True, null=True)
    state = models.CharField(
        _('State'), max_length=150, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True, default=None, db_index=True)
    city = models.CharField(
        _('City'), max_length=150, blank=True, null=True)
    zip_code = models.CharField(
        _('Zip code'), max_length=20, null=True)
    phone = PhoneNumberField(_('Phone'), unique=True,)
    is_phone_verified = models.BooleanField(_('Is Phone Verified'), default=False)
    is_2fa_enabled = models.BooleanField(_('is Two Factor Enabled'), default=False, editable=False)
    legal_business_name = models.CharField(
        _('Legal Business Name'), max_length=150, null=True, blank=True)
    business_dba = models.CharField(
        _('Business DBA'), max_length=150, null=True, blank=True)
    existing_member = models.BooleanField('Account Existed', default=False)
    membership_type = models.CharField(verbose_name=_('Membership Type'),max_length=60, choices=MEMBERSHIP_CHOICES)
    is_verified = models.BooleanField('Is Verified', default=False)
    is_approved = models.BooleanField('Approve User', default=False)
    zoho_contact_id = models.CharField(
        _('Zoho Contact ID'), max_length=100, blank=True, null=True)
    categories = models.ManyToManyField(
        to='MemberCategory',
        related_name='member_category',
        blank=True,
    )
    is_updated_in_crm = models.BooleanField('Is Updated In CRM', default=False)
    profile_photo = models.CharField(
        _('Profile Photo Box ID'), blank=True, null=True, max_length=255)
    profile_photo_sharable_link = models.CharField(
        _('Profile Photo Sharable Link'), blank=True, null=True, max_length=255)
    approved_on = models.DateTimeField(_('Approved on'), blank=True, null=True)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    title = models.CharField(
        _('Title'), max_length=150, null=True, blank=True)
    department = models.CharField(
        _('Department'), max_length=150, null=True, blank=True)
    website = models.CharField(
        _('Website'), max_length=150, null=True, blank=True)
    instagram = models.CharField(
        _('Instagram'), max_length=150, null=True, blank=True)
    facebook = models.CharField(
        _('Facebook'), max_length=150, null=True, blank=True)
    twitter = models.CharField(
        _('Twitter'), max_length=150, null=True, blank=True)
    linkedin = models.CharField(
        _('LinkedIn'), max_length=150, null=True, blank=True)
    about = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
   
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone']

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._meta.get_field('email').db_index = True

    def __str__(self):
        return self.email if self.email else self.username

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_two_factor_devices(self, confirmed_only=True):
        return get_two_factor_devices(self, confirmed_only)

    def get_two_factor_device_dict(self, confirmed_only=True):
        return dict((x.device_id, x.name,) for x in self.get_two_factor_devices(confirmed_only))


class MemberCategory(models.Model):
    """
     Class implementing a categories.
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Member Category')
        verbose_name_plural = _('Member Categories')


class PrimaryPhoneTOTPDevice(AbstractPhoneDevice):
    user = models.OneToOneField(
        User,
        verbose_name=_('User'),
        related_name='primary_phone_totp_device',
        help_text="The user that this device belongs to.",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Primary Phone TOTP Device")
        verbose_name_plural = _("Primary Phone Totp Devices")

    @property
    def phone_number(self):
        return self.user.phone

    @phone_number.setter
    def phone_number(self, value):
        self.user.phone = value

    @property
    def confirmed(self):
        return self.user.is_phone_verified

    @confirmed.setter
    def confirmed(self, value):
        self.user.is_phone_verified = bool(value)
