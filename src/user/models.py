"""
User model defined here.
"""
from binascii import unhexlify
from django.db import models
from django.conf import settings
from django.contrib.auth.models import (AbstractUser,)
from django.utils.translation import ugettext_lazy as _
from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, )
from django.contrib.postgres.fields import (JSONField,)

from django.utils import timezone

# from django_otp.models import Device
from django_otp.oath import totp
from phonenumber_field.modelfields import PhoneNumberField

from integration.apps.twilio import (send_sms,)
from utils.otp import (random_hex_str, key_validator)


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
    key = models.CharField(
        max_length=40,
        validators=[key_validator],
        default=random_hex_str,
        help_text="Hex-encoded secret key"
    )
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

    @property
    def bin_key(self):
        return unhexlify(self.key.encode())

    def verify_otp(self, token):
        # local import to avoid circular import
        no_digits = getattr(settings, 'TOTP_DIGITS', 6)
        try:
            token = int(token)
        except ValueError:
            return False

        for drift in range(-5, 1):
            if totp(self.bin_key, drift=drift, digits=no_digits) == token:
                return True
        return False

    def generate_otp(self):
        # local import to avoid circular import

        """
        Return current TOTP token.
        """
        no_digits = getattr(settings, 'TOTP_DIGITS', 6)
        token = str(totp(self.bin_key, digits=no_digits)).zfill(no_digits)
        return token

    def send_otp(self):
        token = self.generate_otp()
        send_sms(to=self.phone.as_e164, body="Your verification code is "+token)


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

        
    
        
