"""
User model defined here.
"""
from django.db import models
from django.contrib.auth.models import (AbstractUser,)
from django.utils.translation import ugettext_lazy as _
from core.validators import full_domain_validator
from core.mixins.models import (StatusFlagMixin, )
from django.contrib.postgres.fields import (JSONField,)


class User(StatusFlagMixin,AbstractUser):
    """
    Class implementing a custom user model.
    """
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
    phone = models.CharField(
        _('Phone'), max_length=20, null=True)
    legal_business_name = models.CharField(
        _('Legal Business Name'), max_length=150, null=True, blank=True)
    business_dba = models.CharField(
        _('Business DBA'), max_length=150, null=True, blank=True)
    existing_member = models.BooleanField('Account Existed', default=False)
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
        _('Profile Photo Link'), blank=True, null=True, max_length=255)
    approved_on = models.DateTimeField(_('Approved on'), blank=True, null=True)
    approved_by = JSONField(_('Approved by'), null=False, blank=False, default=dict)
    
   
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._meta.get_field('email').db_index = True

    def __str__(self):
        return self.email if self.email else self.username

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


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

        
    
        
