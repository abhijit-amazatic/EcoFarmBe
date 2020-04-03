"""
User model defined here.
"""
from django.db import models
from django.contrib.auth.models import (AbstractUser,)
from django.utils.translation import ugettext_lazy as _
from core.validators import full_domain_validator


class User(AbstractUser):
    """
    Class implementing a custom user model.
    """
    email = models.EmailField(_('Email address'), unique=True)
    username = models.CharField(
        _('Username'), max_length=150, blank=True, null=True)
    full_name = models.CharField(
        _('Full Name'), max_length=255, blank=True, null=True)
    country = models.CharField(
        _('Country'), max_length=150, blank=True, null=True)
    state = models.CharField(
        _('State'), max_length=150, blank=True, null=True)
    date_of_birth = models.DateTimeField()
    city = models.CharField(
        _('City'), max_length=150, blank=True, null=True)
    zip_code = models.CharField(
        _('Zip code'), max_length=20, null=True)
    phone_number = models.CharField(
        _('Mobile Number'), max_length=20, null=True)
    legal_business_name = models.CharField(
        _('Legal Business Name'), max_length=150, null=True)
    business_dba = models.CharField(
        _('Business DBA'), max_length=150, null=True)
    existing_member = models.BooleanField('Account Existed', default=False)
   
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
