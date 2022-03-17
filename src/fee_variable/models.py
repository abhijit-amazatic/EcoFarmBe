"""
Fees model defined here.
"""
from django.conf import settings
from django.db import models
from core.mixins.models import (TimeStampFlagModelMixin)
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField,)

from inventory.models import CustomInventory


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

    program_type = models.CharField(
        verbose_name=_("Program Type"),
        max_length=255,
        choices=PROGRAM_TYPE_CHOICES
    )
    tier = models.CharField(
        verbose_name=_("Tier"),
        max_length=255,
        choices=PROGRAM_TIER_CHOICES
    )
    mcsp_fee_flower_tops = models.DecimalField(
        verbose_name=_("MCSP Fee - Flower Tops ($/lb)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_flower_smalls = models.DecimalField(
        verbose_name=_("MCSP Fee - Flower Smalls ($/lb)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_trims = models.DecimalField(
        verbose_name=_("MCSP Fee - Trims ($/lb)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_concentrates = models.DecimalField(
        verbose_name=_("MCSP Fee - Concentrates (%)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_isolates = models.DecimalField(
        verbose_name=_("MCSP Fee - Isolates (%)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_terpenes = models.DecimalField(
        verbose_name=_("MCSP Fee - Terpenes (%)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_clones = models.DecimalField(
        verbose_name=_("MCSP Fee - Clones ($/pcs)"),
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.program_type

    class Meta:
        verbose_name = _('Vendor Inventory Variable')
        verbose_name_plural = _('Vendor Inventory Variables')


class TaxVariable(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  Tax variables
    """
    dried_flower_tax = models.CharField(verbose_name=_("Dried Flower Tax"), max_length=255,blank=True, null=True)
    dried_leaf_tax = models.CharField(verbose_name=_("Dried Leaf Tax"), max_length=255,blank=True, null=True)
    fresh_plant_tax = models.CharField(verbose_name=_("Fresh Plant Tax"), max_length=255,blank=True, null=True)
    dried_flower_tax_item = models.CharField(verbose_name=_("Dried Flower Tax Item"), max_length=255, blank=True, null=True)
    dried_leaf_tax_item = models.CharField(verbose_name=_("Dried Leaf Tax Item"), max_length=255, blank=True, null=True)
    fresh_plant_tax_item = models.CharField(verbose_name=_("Fresh Plant Tax Item"), max_length=255, blank=True, null=True)
    # cultivar_tax = models.CharField(verbose_name=_("Cultivar Tax"), max_length=255,blank=True, null=True)
    # trim_tax = models.CharField(verbose_name=_("Trim Tax"), max_length=255,blank=True, null=True)
    # cultivar_tax_item = models.CharField(verbose_name=_("Cultivar Tax Item"), max_length=255, blank=True, null=True)
    # trim_tax_item = models.CharField(verbose_name=_("Trim Tax Item"), max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.dried_flower_tax} | {self.dried_leaf_tax} | {self.fresh_plant_tax}'

    class Meta:
        verbose_name = _('Tax Variable')
        verbose_name_plural = _('Tax Variables')


class CampaignVariable(TimeStampFlagModelMixin,models.Model):
    """
    Zoho campaign variables.
    """
    from_email = models.EmailField(verbose_name=_("From Email"), max_length=255, blank=True, null=True)
    mailing_list_id = ArrayField(models.CharField(max_length=255), blank=True, null=True)

    class Meta:
        verbose_name = _('Campaign Variable')
        verbose_name_plural = _('Campaign Variables')

class QRCodeVariable(TimeStampFlagModelMixin,models.Model):
    """
    QR Code related variables.
    """
    qr_code_size = models.IntegerField(verbose_name=_("QR Code Size"),null=True, blank=True,help_text="The width and height of the QR code displayed on your image.This is the minimum pixel size of your QR code image.Actual size of the QR code can be slightly bigger depending on data and configuration.")
    
    class Meta:
        verbose_name = _('QR Code Variable')
        verbose_name_plural = _('QR Code Variables')

     

        
class VendorInventoryDefaultAccounts(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  CustomInventory variables
    """
    ZOHO_ORG_EFD = 'efd'
    ZOHO_ORG_EFL = 'efl'
    ZOHO_ORG_EFN = 'efn'
    ZOHO_ORG_CHOICES = (
        (ZOHO_ORG_EFD, _('Thrive Society (EFD LLC)')),
        (ZOHO_ORG_EFL, _('Eco Farm Labs (EFL LLC)')),
        (ZOHO_ORG_EFN, _('Eco Farm Nursery (EFN LLC)')),
    )

    zoho_organization = models.CharField(_('Zoho Organization'), unique=True, choices=ZOHO_ORG_CHOICES, max_length=20)

    sales_account = models.CharField(verbose_name=_("Default Sales Account"), max_length=255, null=True, blank=True)
    purchase_account = models.CharField(verbose_name=_("Default Purchase Account"), max_length=255, null=True, blank=True)
    inventory_account = models.CharField(verbose_name=_("Default inventory Account"), max_length=255, null=True, blank=True)

    def __str__(self):
        return self.zoho_organization

    def get_new_item_accounts_dict(self):
        resp = {}
        if self.sales_account:
            resp['account_id'] = self.sales_account
        if self.purchase_account:
            resp['purchase_account_id'] = self.purchase_account
        if self.inventory_account:
            resp['inventory_account_id'] = self.inventory_account
        return resp

    class Meta:
        verbose_name = _('Vendor Inventory Default Accounts')
        verbose_name_plural = _('Vendor Inventory Default Accounts')


class VendorInventoryCategoryAccounts(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  CustomInventory variables
    """
    default_accounts = models.ForeignKey(VendorInventoryDefaultAccounts, verbose_name=_('Default Accounts'), related_name='category_accounts_set', on_delete=models.CASCADE)
    item_category = models.CharField(_('Item Category'), choices=CustomInventory.CATEGORY_NAME_CHOICES, max_length=50)

    sales_account = models.CharField(verbose_name=_("Sales Account"), max_length=255, null=True, blank=True)
    purchase_account = models.CharField(verbose_name=_("Purchase Account"), max_length=255, null=True, blank=True)
    inventory_account = models.CharField(verbose_name=_("inventory Account"), max_length=255, null=True, blank=True)

    def __str__(self):
        return self.item_category

    def get_new_item_accounts_dict(self):
        resp = {}
        if self.sales_account:
            resp['account_id'] = self.sales_account
        if self.purchase_account:
            resp['purchase_account_id'] = self.purchase_account
        if self.inventory_account:
            resp['inventory_account_id'] = self.inventory_account
        return resp

    class Meta:
        unique_together = (('default_accounts', 'item_category'), )
        verbose_name = _('Vendor Inventory Category Accounts')
        verbose_name_plural = _('Vendor Inventory Category Accounts')


class Agreement(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing Agreement Model.
    """
    name = models.CharField(_('Name'), unique=True, max_length=255)
    box_source_file_id = models.CharField(_('Box Source File Id'), unique=True, max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Agreement')
        verbose_name_plural = _('Agreements')



class Program(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing Agreement Model.
    """
    name = models.CharField(_('Name'), unique=True, max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Program')
        verbose_name_plural = _('Programs')


class ProgramProfileCategoryAgreement(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing Program, Profile Category and Agreement related Model.
    """
    profile_category = models.ForeignKey(
        'brand.ProfileCategory',
        verbose_name=_('Profile Category'),
        related_name='program_profile_category_agreement_set',
        on_delete=models.CASCADE,
    )
    program = models.ForeignKey(
        Program,
        verbose_name=_('Program'),
        related_name='program_profile_category_agreement_set',
        on_delete=models.CASCADE,
    )
    agreement = models.ForeignKey(
        Agreement,
        verbose_name=_('Agreement'),
        related_name='program_profile_category_agreement_set',
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return f"{self.program} {self.profile_category}"

    class Meta:
        unique_together = ('program', 'profile_category')
        verbose_name = _('Program Profile Category Agreement')
        verbose_name_plural = _('Program Profile Category Agreement')


class FileLink(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing file link variables.
    """

    LABEL_CHOICES = (
        ('order_page_sales_agreement', _('Order Page Sales Agreement')),
    )

    label = models.CharField(_('Label'), unique=True, choices=LABEL_CHOICES, max_length=255)
    # box_file_id = models.CharField(_('BOX File ID'), max_length=255)
    url = models.URLField(_('URL'), max_length=255)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = _('File Link')
        verbose_name_plural = _('File Links')
