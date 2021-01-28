"""
Model for integrations.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _


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


class OrderVariable(models.Model):
    """
    Class implementing  order variables
    """
    PROGRAM_TYPE_GOLD = 'gold'
    PROGRAM_TYPE_SILVER = 'silver'
    PROGRAM_TYPE_CHOICES = (
        (PROGRAM_TYPE_GOLD, _('Gold')),
        (PROGRAM_TYPE_SILVER, _('Silver')),
    )
    program_type = models.CharField(verbose_name=_("Program"), max_length=255, choices=PROGRAM_TYPE_CHOICES)
    mcsp_fee = models.CharField(verbose_name=_("MCSP Fee(%)"), max_length=255,blank=True, null=True)
    net_7_14 = models.CharField(verbose_name=_("Net 7-14(%)"), max_length=255,blank=True, null=True)
    net_14_30 = models.CharField(verbose_name=_("Net 14-30(%)"), max_length=255,blank=True, null=True)
    cash = models.CharField(verbose_name=_("Cash(%)"), max_length=255,blank=True, null=True)
    transportation_fee = models.CharField(verbose_name=_("Transportation Fee/Mile($)"), max_length=255,blank=True, null=True)
    
    def __str__(self):
        return self.program_type

    class Meta:
        verbose_name = _('Order Variable')
      

        
