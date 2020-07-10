"""
Inventory Model
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )


class Inventory(models.Model):
    """
    Inventory Model Class
    """
    cultivar = models.ForeignKey(Cultivar, verbose_name=_('Cultivar'), blank=True, null=True,
                                related_name='cultivar', on_delete=models.PROTECT)
    labtest = models.ForeignKey(LabTest, verbose_name=_('LabTest'), blank=True, null=True,
                                related_name='labtest', on_delete=models.PROTECT)
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
    # cf_potency = models.FloatField(_('Potency'), blank=True, null=True)
    # cf_cbd = models.FloatField(_('CBD'), blank=True, null=True)
    cf_cultivar_type = models.CharField(_('Cultivar Type'), blank=True, null=True, max_length=50)
    cf_procurement_rep = models.CharField(_('Procurement Rep'), blank=True, null=True, max_length=50)
    cf_cfi_published = models.BooleanField(_('CFI_Published'), blank=True, null=True)
    cf_ifp_farm = models.BooleanField(_('IFP_Farm'), blank=True, null=True)
    cf_vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=50)
    cf_procurement_confirmed = models.CharField(_('PnC'), blank=True, null=True, max_length=50)
    cf_marge_per_unit = models.FloatField(_('Margin Per Unit'), blank=True, null=True)
    cf_lpn = models.CharField(_('LPN'), blank=True, null=True, max_length=50)
    cf_received_date = models.CharField(_('Received Date'), blank=True, null=True, max_length=50)
    cf_pending_sale_1_1 = models.CharField(_('Pending Sale 1'), blank=True, null=True, max_length=100)
    cf_pending_sale_2 = models.CharField(_('Pending Sale 2'), blank=True, null=True, max_length=100)
    cf_pending_sale_3 = models.CharField(_('Pending Sale 3'), blank=True, null=True, max_length=100)
    cf_metrc_manifest_number = models.TextField(_('Metrc Manifest Number'), blank=True, null=True)
    cf_harvest = models.CharField(_('Harvest'), blank=True, null=True, max_length=50)
    cf_metrc_packages = models.TextField(_('Metrc Package'), blank=True, null=True)
    cf_payment_terms = models.CharField(_('Payment Terms'), blank=True, null=True, max_length=255)
    cf_lab_test_link = models.URLField(_('Lab Test Link'), blank=True, null=True, max_length=255)
    # cf_d_8_thc = models.FloatField(_('D8_THC'), blank=True, null=True)
    # cf_thca = models.FloatField(_('THCA'), blank=True, null=True)
    # cf_cbda = models.FloatField(_('CBDA'), blank=True, null=True)
    # cf_cbn = models.FloatField(_('CBN'), blank=True, null=True)
    # cf_cbc = models.FloatField(_('CBC'), blank=True, null=True)
    # cf_cbca = models.FloatField(_('CBCA'), blank=True, null=True)
    # cf_cbga = models.FloatField(_('CBGA'), blank=True, null=True)
    # cf_cbl = models.FloatField(_('CBL'), blank=True, null=True)
    # cf_thcva = models.FloatField(_('THCVA'), blank=True, null=True)
    # cf_cbdv = models.FloatField(_('CBDV'), blank=True, null=True)
    cf_testing_type = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    cf_pesticide_summary = models.CharField(_('Pesticide Summary'), blank=True, null=True, max_length=255)
    cf_farm_price = models.FloatField(_('Farm Price'), blank=True, null=True)
    cf_next_harvest_date = models.DateField(auto_now=False, blank=True, null=True, default=None)
    # cf_alpha_pinene = models.FloatField(_('ALPHA PIENE'), blank=True, null=True)
    # cf_myrcene = models.FloatField(_('MYRECENE'), blank=True, null=True)
    # cf_ocimene = models.FloatField(_('OCIMENE'), blank=True, null=True)
    # cf_terpinolene = models.FloatField(_('TERPINOLENE'), blank=True, null=True)
    # cf_beta_caryophyllene = models.FloatField(_('BETA CARYOPHYLLENE'), blank=True, null=True)
    # cf_alpha_humulene = models.FloatField(_('ALPHA HUMULENE'), blank=True, null=True)
    # cf_linalool = models.FloatField(_('LINALOOL'), blank=True, null=True)
    # cf_r_limonene = models.FloatField(_('LIMONENE'), blank=True, null=True)
    # cf_alpha_terpineol = models.FloatField(_('ALPHA TERPINEOL'), blank=True, null=True)
    # cf_valencene = models.FloatField(_('VALENECENE'), blank=True, null=True)
    # cf_geraniol = models.FloatField(_('GERANIOL'), blank=True, null=True)
    package_details = JSONField(blank=True, null=True, default=dict)
    documents = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    batches = ArrayField(JSONField(default=dict), blank=True, null=True)
    
    def __str__(self):
        return self.name