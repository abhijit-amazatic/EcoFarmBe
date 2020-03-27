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
    website_url = models.CharField(_('Website URL'), max_length=255,
                                   null=True, validators=[full_domain_validator])
    mobile_number = models.CharField(
        _('Mobile Number'), max_length=20, null=True)
    completed_onboarding = models.BooleanField('Completed Onboarding', default=False)
    completed_tour = models.BooleanField('Completed Tour', default=False)
    associated_hs_deal_id =  models.CharField(_('HS Deal ID'),max_length=50, null=True, blank=True)
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
