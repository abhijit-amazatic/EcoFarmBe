"""
Fees model defined here.
"""
from django.conf import settings
from django.db import models
from core.mixins.models import (TimeStampFlagModelMixin)
from django.utils.translation import ugettext_lazy as _


class OrderVariable(TimeStampFlagModelMixin,models.Model):
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
    
    tier = models.CharField(verbose_name=_("Tier"), max_length=255, choices=PROGRAM_TIER_CHOICES)
    mcsp_fee = models.CharField(verbose_name=_("MCSP Fee(%)"), max_length=255,blank=True, null=True)
    net_7_14 = models.CharField(verbose_name=_("Net 7-14(%)"), max_length=255,blank=True, null=True)
    net_14_30 = models.CharField(verbose_name=_("Net 14-30(%)"), max_length=255,blank=True, null=True)
    cash = models.CharField(verbose_name=_("Cash(%)"), max_length=255,blank=True, null=True)
    transportation_fee = models.CharField(verbose_name=_("Transportation Fee/Mile($)"), max_length=255,blank=True, null=True)
    
    def __str__(self):
        return self.tier

    class Meta:
        verbose_name = _('Order Variable')
        verbose_name_plural = _('Order Variables')      

        

