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
    farm_url = models.CharField(_('Farm URL'), max_length=255,
                                   null=True, validators=[full_domain_validator])

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
