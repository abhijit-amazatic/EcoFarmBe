"""
Model for integrations.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin)

class Integration(models.Model):
    name = models.CharField(_('Name'), max_length=255, unique=True)
    client_id = models.CharField(_('Client ID'), max_length=255, blank=True, null=True)
    client_secret = models.CharField(_('Client Secret'), max_length=255, blank=True, null=True)
    access_token = models.CharField(_('Access Token'), max_length=255)
    refresh_token = models.CharField(_('Refresh Token'), max_length=255)
    access_expiry = models.DateTimeField(_('Access Expiry'), blank=True, null=True)
    refresh_expiry = models.DateTimeField(_('Refresh Expiry'), blank=True, null=True)
    expiry_time = models.BigIntegerField(_('expiry_time_crm'), blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('integration')
        verbose_name_plural = _('integrations')


        
class ConfiaCallback(TimeStampFlagModelMixin, models.Model):
    """
    Model to save confia callback data after onboarding.
    """
    partner_company_id = models.CharField(_('partnerCompanyId'), max_length=255, blank=True, null=True)
    confia_member_id = models.CharField(_('confiaMemberId'), max_length=255, blank=True, null=True)
    status = models.CharField(_('status'), max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.partner_company_id if self.partner_company_id else ""

    class Meta:
        verbose_name = _('Confia Onboarding')
