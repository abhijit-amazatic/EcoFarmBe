"""
User model defined here.
"""
from django.conf import settings
from django.contrib.auth.models import (AbstractUser,)
from django.contrib.postgres.fields import (JSONField,)
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField,)

from phonenumber_field.modelfields import PhoneNumberField
from ckeditor.fields import RichTextField


from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin)
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
    recovery_email = models.EmailField(_('Recovery Email address'), blank=True, null=True)
    alternate_email = models.EmailField(_('Alternate Email address'), blank=True, null=True)
    phone = PhoneNumberField(_('Phone'), unique=True,)
    is_phone_verified = models.BooleanField(_('Is Phone Verified'), default=False)
    is_2fa_enabled = models.BooleanField(_('is Two Factor Enabled'), default=False, editable=False)
    legal_business_name = ArrayField(models.CharField(max_length=255, blank=True),blank=True, null=True, default=list)
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
        setattr(self, 'save_user', True)

    @property
    def confirmed(self):
        return self.user.is_phone_verified

    @confirmed.setter
    def confirmed(self, value):
        self.user.is_phone_verified = bool(value)
        setattr(self, 'save_user', True)

    @property
    def is_removable(self):
        return False

    def save(self, *args, **kwargs):
        if getattr(self, 'save_user', False):
            self.user.save()
            setattr(self, 'save_user', False)
        return super().save(*args, **kwargs)



class TermsAndCondition(TimeStampFlagModelMixin, models.Model):
    """
    Class implementing terms and condition.
    """
    PROFILE_TYPE_SELLER = 'seller'
    PROFILE_TYPE_BUYER = 'buyer'
    PROFILE_TYPE_OTHER = 'other'
    PROFILE_TYPE_CHOICES = (
        (PROFILE_TYPE_SELLER, _('Seller')),
        (PROFILE_TYPE_BUYER, _('Buyer')),
        (PROFILE_TYPE_OTHER, _('Other')),
    )
    profile_type = models.CharField(verbose_name=_("Profile Type"), max_length=255, choices=PROFILE_TYPE_CHOICES)
    terms_and_condition = RichTextField(verbose_name=_("Terms And Condition"))
    publish_from = models.DateField(verbose_name=_("Publish From"))

    def __str__(self):
        return f'{self.id} | {self.profile_type} | {self.publish_from}'

    class Meta:
        verbose_name = _('Terms And Condition')


class TermsAndConditionAcceptance(TimeStampFlagModelMixin, models.Model):
    """
    Class implementing a terms and condition acceptance.
    """
    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        related_name='terms_and_condition_acceptances',
        on_delete=models.CASCADE,
    )
    terms_and_condition = models.ForeignKey(
        TermsAndCondition,
        verbose_name=_('Terms And Condition'),
        related_name='terms_and_condition_acceptances',
        on_delete=models.PROTECT,
    )
    is_accepted = models.BooleanField(verbose_name=_("Is Accepted"),)
    ip_address = models.GenericIPAddressField(verbose_name=_("IP Address"))
    user_agent = models.TextField(_("User Agent"),max_length=1000,)
    hostname = models.CharField(verbose_name=_("Hostname"), max_length=255)


    def __str__(self):
        return f'{self.user} | {self.terms_and_condition}'

    class Meta:
        verbose_name = _('Terms And Condition Acceptance')
        verbose_name_plural = _('Terms And Condition Acceptances')


@receiver(models.signals.pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    """
    Deletes old file.
    """
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if not instance.phone == old_instance.phone:
        instance.is_phone_verified = False
    if not instance.email == old_instance.email:
        instance.is_verified = False


@receiver(models.signals.post_save, sender=User)
def post_save_user(sender, instance, created, **kwargs):
    """
    Deletes old file.
    """
    try:
        instance.primary_phone_totp_device
    except sender.primary_phone_totp_device.RelatedObjectDoesNotExist:
        PrimaryPhoneTOTPDevice.objects.create(user=instance)
