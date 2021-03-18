"""
Brand related schemas defined here.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission as DjPermission
from django.contrib.postgres.fields import (ArrayField, JSONField, HStoreField,)
from django.contrib.contenttypes.fields import (GenericRelation, )
from django.conf import settings
from django.utils import timezone


class PermissionGroup(models.Model):
    """
    The permission Group.
    """
    name = models.CharField(
        _('Name'),
        max_length=100,
        unique=True,
    )

    class Meta:
        verbose_name = _('Permission Group')
        verbose_name_plural = _('Permission Groups')
        ordering = ('name',)

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    The permissions.
    """
    PERMISSION_TYPE_ORGANIZATIONAL = 'organizational'
    PERMISSION_TYPE_INTERNAL = 'internal'
    PERMISSION_TYPE_CHOICES = (
        (PERMISSION_TYPE_ORGANIZATIONAL, _('Organizational')),
        (PERMISSION_TYPE_INTERNAL, _('Internal')),
    )

    id = models.CharField(
        _('Id'),
        max_length=100,
        unique=True,
        primary_key=True,
    )
    name = models.CharField(
        _('Name'),
        max_length=100,
    )
    type = models.CharField(
        _('Type'),
        choices=PERMISSION_TYPE_CHOICES,
        max_length=100,
    )

    description = models.TextField(_('description'), null=True, blank=True)
    group = models.ForeignKey(
        PermissionGroup,
        verbose_name=_('Group'),
        related_name='permissions',
        on_delete=models.PROTECT
    )

    # def save(self, *args, **kwargs):
    #     self.group = PERMISSION_GROUP_MAP[self.codename]
    #     return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ('group__name', 'id')

    def __str__(self):
        return f"{self.group} | {self.name}"

    def natural_key(self):
        return (self.name,)


class InternalRole(models.Model):
    """
    Stores Organization User's Roles.
    """
    name = models.CharField(
        verbose_name=_('Name'),
        max_length=60,
        unique=True
    )
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('Permissions'),
        blank=True,
    )
    profile_categories = models.ManyToManyField(
        'brand.ProfileCategory',
        verbose_name=_('Profile Categories'),
        blank=True,
    )

    owned_profiles_only = models.BooleanField(_('Owned Profiles Only'), default=True,)

    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        verbose_name = _('Internal Role')
        verbose_name_plural = _('Internal Roles')
