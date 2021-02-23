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
    PROGRAM_TIER_GOLD = 'gold'
    PROGRAM_TIER_SILVER = 'silver'
    PROGRAM_TIER_BRONZE = 'bronze'
    PROGRAM_TIER_CHOICES = (
        (PROGRAM_TIER_GOLD, _('Gold')),
        (PROGRAM_TIER_SILVER, _('Silver')),
        (PROGRAM_TIER_BRONZE, _('Bronze')),
        
    )

    PROGRAM_TYPE_IFP = 'ifp'
    PROGRAM_TYPE_SELLER = 'seller'
    PROGRAM_TYPE_CHOICES = (
        (PROGRAM_TYPE_IFP, _('IFP Program')),
        (PROGRAM_TYPE_SELLER, _('Seller Program')),
    )
    
    program_type = models.CharField(verbose_name=_("Program Type"), max_length=255, choices=PROGRAM_TYPE_CHOICES)
    tier = models.CharField(verbose_name=_("Tier"), max_length=255, choices=PROGRAM_TIER_CHOICES)
    mcsp_fee = models.CharField(verbose_name=_("MCSP Fee(%)"), max_length=255,blank=True, null=True)
    net_7_14 = models.CharField(verbose_name=_("Net 7-14(%)"), max_length=255,blank=True, null=True)
    net_14_30 = models.CharField(verbose_name=_("Net 14-30(%)"), max_length=255,blank=True, null=True)
    cash = models.CharField(verbose_name=_("Cash(%)"), max_length=255,blank=True, null=True)
    transportation_fee = models.CharField(verbose_name=_("Transportation Fee/Mile($)"), max_length=255,blank=True, null=True)
    
    def __str__(self):
        return self.program_type

    class Meta:
        verbose_name = _('Fees & Variables')
        verbose_name_plural = _('Fees & Variables')      

        
