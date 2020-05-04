"""
Inventory Model
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)


class Inventory(models.Model):
    """
    Inventory Model Class
    """
    created_time = models.DateTimeField(auto_now=False)
    last_modified_time = models.DateTimeField(auto_now=False)
    item_id = models.CharField(_('Item ID'), primary_key=True, max_length=50)
    item_type = models.CharField(_('Item Type'), blank=True, null=True, max_length=50)
    name = models.CharField(_('Name'), max_length=255)
    sku = models.CharField(_('SKU'), blank=True, null=True, max_length=100, db_index=True)
    manufacturer = models.CharField(_('Manufracturer'), blank=True, null=True, max_length=100)
    category_name = models.CharField(_('Category Name'), max_length=50)
    category_id = models.CharField(_('Category ID'), blank=True, null=True, max_length=50)
    vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=255)
    unit = models.CharField(_('Unit'), blank=True, null=True, max_length=20)
    status = models.CharField(_('Status'), blank=True, null=True, max_length=20)
    zcrm_product_id = models.CharField(_('CRM Product ID'), blank=True, null=True, max_length=50)
    is_combined_product = models.BooleanField(_('Is Combined Product'))
    account_id = models.CharField(_('Account ID'), blank=True, null=True, max_length=50)
    account_name = models.CharField(_('Account Name'), blank=True, null=True, max_length=50)
    description = models.TextField(_('Description'), blank=True, null=True)
    brand = models.CharField(_('Brand'), blank=True, null=True, max_length=50)
    price = models.FloatField(_('Price'))
    purchase_rate = models.FloatField(_('Purchase Rate'))
    tax_id = models.CharField(_('Tax ID'), blank=True, null=True, max_length=50)
    tax_name = models.CharField(_('Tax Name'), blank=True, null=True, max_length=50)
    tax_type = models.CharField(_('Tax Type'), blank=True, null=True, max_length=50)
    tax_percentage = models.FloatField(_('Tax Percentage'))
    purchase_account_name = models.CharField(_('Purchase Account Name'), blank=True, null=True, max_length=255)
    product_type = models.CharField(_('Product Type'), blank=True, null=True, max_length=100)
    is_taxable = models.BooleanField(_('Is Taxable'))
    is_returnable = models.BooleanField(_('Is Returnable'))
    tax_exemption_code = models.CharField(_('Tax Excemption Code'), blank=True, null=True, max_length=100)
    total_initial_stock = models.FloatField(_('Total Initial Stock'), blank=True, null=True)
    stock_on_hand = models.FloatField(_('Stock On Hand'), blank=True, null=True)
    available_stock = models.FloatField(_('Availabe Stock'), blank=True, null=True)
    cf_strain_name = models.CharField(_('Strain Name'), blank=True, null=True, max_length=255)
    cf_cultivation_type = models.CharField(_('Cultivation Type'), blank=True, null=True, max_length=100)
    cf_cannabis_grade_and_category = models.CharField(_('Cannabis Grade and Category'), blank=True, null=True, max_length=100)
    cf_client_code = models.CharField(_('Client Code'), blank=True, null=True, max_length=50)
    cf_lab_file = models.URLField(_('Lab File'), blank=True, null=True, max_length=255)
    cf_pending_sale = models.CharField(_('Pending Sale'), blank=True, null=True, max_length=255)
    cf_potency = models.FloatField(_('Potency'), blank=True, null=True)
    cf_cbd = models.FloatField(_('Potency'), blank=True, null=True)
    cf_cultivar_type = models.CharField(_('Cultivar Type'), blank=True, null=True, max_length=50)
    cf_procurement_rep = models.CharField(_('Procurement Rep'), blank=True, null=True, max_length=50)
    package_details = JSONField(blank=True, null=True, default=dict)
    documents = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    batches = ArrayField(JSONField(default=dict), blank=True, null=True)
    
    def __str__(self):
        return self.name