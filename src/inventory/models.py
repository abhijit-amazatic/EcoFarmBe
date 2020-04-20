"""
Inventory Model
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Inventory(mdoes.Model):
    """
    Inventory Model Class
    """
    name = models.CharField(_('Name'), max_length=255)
    sku = models.CharField(_('SKU'), max_length=100, db_index=True)
    manufacturer = models.CharField(_('Manufracturer'), blank=True, null=True, max_length=100)
    category_name = models.CharField(_('Category Name'), max_length=50)
    vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=255)
    unit = models.CharField(_('Unit'), blank=True, null=True, max_length=20)
    status = models.CharField(_('Status'), blank=True, null=True, max_length=20)
    is_combined_product = models.BooleanField(_('Is Combined Product'))
    description = models.TextField(_('Description'), blank=True, null=True)
    brand = models.CharField(_('Brand'), blank=True, null=True, max_length=50)
    price = models.IntegerField(_('Price'))
    purchase_rate = models.IntegerField(_('Purchase Rate'))
    tax_percentage = models.FloatField(_('Tax Percentage'))
    purchase_account_name = models.CharField(_('Purchase Account Name'), blank=True, null=True, max_length=255)
    product_type = models.CharField(_('Product Type'), blank=True, null=True, max_length=100)
    is_taxable = models.BooleanField(_('Is Taxable'))
    is_returnable = models.BooleanField(_('Is Returnable'))
    tax_exemption_code = models.CharField(_('Tax Excemption Code'), blank=True, null=True, max_length=100)
    total_initial_stock = models.FloatField(_('Total Initial Stock'), blank=True, null=True)
    stock_on_hand = models.FloatField(_('Stock On Hand'))
    available_stock = models.FloatField(_('Availabe Stock'))
    cf_strain_name = models.CharField(_('Strain Name'), blank=True, null=True, max_length=255)
    cf_cultivation_type = models.CharField(_('Cultivation Type'), blank=True, null=True, max_length=100)
    cf_cannabis_grade_and_category = models.CharField(_('Cannabis Grade and Category'), blank=True, null=True, max_length=100)
    cf_client_code = models.CharField(_('Client Code'), blank=True, null=True, max_length=50)
    cf_lab_file = models.URLField(_('Lab File'), blank=True, null=True, max_length=255)
    cf_pending_sale = models.CharField(_('Pending Sale'), blank=True, null=True, max_length=255)
    cf_potency = models.CharField(_('Potency'), blank=True, null=True, max_length=50)
    
    def __str__(self):
        return self.name