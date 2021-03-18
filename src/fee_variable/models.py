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
        
class CustomInventoryVariable(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  CustomInventory variables
    """
    PROGRAM_TIER_GOLD = 'gold'
    PROGRAM_TIER_SILVER = 'silver'
    PROGRAM_TIER_BRONZE = 'bronze'
    PROGRAM_TIER_NO_TIER = 'no_tier'
    PROGRAM_TIER_CHOICES = (
        (PROGRAM_TIER_GOLD, _('Gold')),
        (PROGRAM_TIER_SILVER, _('Silver')),
        (PROGRAM_TIER_BRONZE, _('Bronze')),
        (PROGRAM_TIER_NO_TIER, _('No Tier')),
        
    )
    PROGRAM_TYPE_IFP = 'ifp'
    PROGRAM_TYPE_IBP = 'ibp'
    PROGRAM_TYPE_CHOICES = (
        (PROGRAM_TYPE_IFP, _('IFP Program')),
        (PROGRAM_TYPE_IBP, _('IBP Program')),
    )

    
    program_type = models.CharField(verbose_name=_("Program Type"), max_length=255, choices=PROGRAM_TYPE_CHOICES)
    tier = models.CharField(verbose_name=_("Tier"), max_length=255, choices=PROGRAM_TIER_CHOICES)
    mcsp_fee = models.CharField(verbose_name=_("MCSP Fee"), max_length=255,blank=True, null=True)
    
    def __str__(self):
        return self.program_type

    class Meta:
        verbose_name = _('Vendor Inventory Variable')
        verbose_name_plural = _('Vendor Inventory Variables')      
       

class TaxVariable(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  Tax variables
    """
    cultivar_tax = models.CharField(verbose_name=_("Cultivar Tax"), max_length=255,blank=True, null=True)
    trim_tax = models.CharField(verbose_name=_("Trim Tax"), max_length=255,blank=True, null=True)
    cultivar_tax_item = models.CharField(verbose_name=_("Cultivar Tax Item"), max_length=255, blank=True, null=True)
    trim_tax_item = models.CharField(verbose_name=_("Trim Tax Item"), max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f'{self.cultivar_tax} | {self.trim_tax}'

    class Meta:
        verbose_name = _('Tax Variable')
        verbose_name_plural = _('Tax Variables')      
        
