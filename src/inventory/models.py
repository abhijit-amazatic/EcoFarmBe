"""
Inventory Model
"""
from django import forms
from django.contrib.contenttypes.fields import (GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)

from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from core.mixins.models import (TimeStampFlagModelMixin, )
from user.models import (User, )
from .fields import (ChoiceArrayField,)

class Documents(TimeStampFlagModelMixin, models.Model):
    """
    Documents model.
    """
    OPTIMIZING = 'OPTIMIZING' # File is compressing.
    REQUESTED = 'REQUESTED' # Pre-Signed url requested.
    AVAILABLE = 'AVAILABLE' # File is available.
    UPLOADING = 'UPLOADING' # Uploading file to s3.
    ERROR = 'ERROR'
    STATUS_CHOICES = (
        (OPTIMIZING, 'Optimizing'),
        (REQUESTED, 'Requested'),
        (AVAILABLE, 'Available'),
        (UPLOADING, 'Uploading'),
        (ERROR, 'Error'),
    )
    
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    sku = models.CharField(_('SKU'), max_length=255, blank=True, null=True, db_index=True)
    name = models.CharField(_('Name'), max_length=255)
    size = models.CharField(_('File Size'), blank=True, null=True, max_length=100)
    file_type = models.CharField(_('File Type'), blank=True, null=True, max_length=50)
    path = models.CharField(_('File Path'), blank=True, null=True, max_length=500)
    status = models.CharField(_('Status'), default=UPLOADING, max_length=50, db_index=True, choices=STATUS_CHOICES)
    box_url = models.CharField(_('Box Url'), blank=True, null=True, max_length=500)
    thumbnail_url = models.CharField(_('Thumbnail Url'), blank=True, null=True, max_length=500)
    mobile_url = models.CharField(_('Mobile Url'), blank=True, null=True, max_length=500)
    box_id = models.CharField(_('Box ID'), blank=True, null=True, max_length=100)
    is_primary = models.BooleanField(_('Is Primary Image'), default=False)
    doc_type = models.CharField(_('Doc Type'), blank=True, null=True, max_length=50)
    order = models.IntegerField(_('Order'), blank=True, null=True)



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
    image_name = models.CharField(_('Image Name'), blank=True, null=True, max_length=100)
    image_type = models.CharField(_('Image Type'), blank=True, null=True, max_length=50)
    manufacturer = models.CharField(_('Manufracturer'), blank=True, null=True, max_length=100)
    category_name = models.CharField(_('Category Name'), max_length=50)
    category_id = models.CharField(_('Category ID'), blank=True, null=True, max_length=50)
    vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=255)
    unit = models.CharField(_('Unit'), blank=True, null=True, max_length=20)
    status = models.CharField(_('Status'), blank=True, null=True, max_length=20)
    zcrm_product_id = models.CharField(_('CRM Product ID'), blank=True, null=True, max_length=50)
    is_combined_product = models.BooleanField(_('Is Combined Product'), blank=True, null=True)
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
    is_taxable = models.BooleanField(_('Is Taxable'), blank=True, null=True)
    is_returnable = models.BooleanField(_('Is Returnable'), blank=True, null=True)
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
    cf_cultivar_type = models.CharField(_('Cultivar Type'), blank=True, null=True, max_length=50)
    cf_procurement_rep = models.CharField(_('Procurement Rep'), blank=True, null=True, max_length=50)
    cf_cfi_published = models.BooleanField(_('CFI_Published'), blank=True, null=True)
    cf_ifp_farm = models.BooleanField(_('IFP_Farm'), blank=True, null=True)
    cf_vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=50)
    county_grown = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
    appellation = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
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
    cf_testing_type = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    cf_pesticide_summary = models.CharField(_('Pesticide Summary'), blank=True, null=True, max_length=255)
    cf_next_harvest_date = models.DateField(auto_now=False, blank=True, null=True, default=None)
    purchase_account_id = models.CharField(_('Purchase Account Id'), blank=True, null=True, max_length=100)
    inventory_account_id = models.CharField(_('Inventory Account Id'), blank=True, null=True, max_length=100)
    inventory_account_name = models.CharField(_('Inventory Account Name'), blank=True, null=True, max_length=100)
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True,default=list)
    available_for_sale_stock = models.FloatField(_('Available For Sale Stock'), blank=True, null=True)
    actual_available_for_sale_stock = models.FloatField(_('Actual Available For Sale Stock'), blank=True, null=True)
    actual_available_stock = models.FloatField(_('Actual Available For Sale Stock'), blank=True, null=True)
    cf_manufacturing_date = models.DateField(auto_now=False, blank=True, null=True, default=None)
    cf_batch_blending = models.CharField(_('Batch Blending'), blank=True, null=True, max_length=100)
    cf_lab_testing_status = models.URLField(_('Lab Testing Status'), blank=True, null=True, max_length=255)
    cf_qa_intake_grading_sheet_id = models.CharField(_('Qa Intake Grading Sheet Id'), blank=True, null=True, max_length=100)
    cf_administrative_hold = models.CharField(_('Administrative Hold'), blank=True, null=True, max_length=100)
    cf_batch_notes = models.TextField(_('Batch Notes'), blank=True, null=True)
    cf_lab_test_results_box_url = models.URLField(_('Lab Test Results Box Url'), blank=True, null=True, max_length=255)
    track_batch_number = models.CharField(_('Track Batch Number'), blank=True, null=True, max_length=100)
    cf_date_available = models.DateField(auto_now=False, blank=True, null=True, default=None)
    cf_status = models.CharField(_('Status'), blank=True, null=True, max_length=100)
    cf_lab_test_sample_id = models.CharField(_('cf_lab_test_sample_id'), blank=True, null=True, max_length=100)
    cf_quantity_estimate = models.FloatField(_('cf_quantity_estimate'), blank=True, null=True)
    cf_metrc_source_package_id = models.CharField(_('cf_metrc_source_package_id'), blank=True, null=True, max_length=100)
    cf_market_feedback = models.TextField(_('cf_market_feedback'), blank=True, null=True)
    cf_sample_in_house = models.CharField(_('Sample In House'), blank=True, null=True, max_length=100)
    cf_seller_position = models.CharField(_('Seller Position'), blank=True, null=True, max_length=100)
    cf_farm_price = models.CharField(_('Farm Price'), blank=True, null=True, max_length=100)
    cf_farm_price_2 = models.FloatField(_('Farm Price'), blank=True, null=True)
    cf_minimum_quantity = models.FloatField(_('Minimum Quantity'), blank=True, null=True)
    cf_available_date = models.DateField(auto_now=False, blank=True, null=True, default=None)
    cf_trim_qty_lbs = models.FloatField(_('Trim Quantity Used (lbs)'), blank=True, null=True)
    cf_batch_qty_g = models.IntegerField(_('Batch Quantity (g)'), null=True, blank=True)
    package_details = JSONField(blank=True, null=True, default=dict)
    documents = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    batches = ArrayField(JSONField(default=dict), blank=True, null=True)
    pre_tax_price = models.FloatField(_('pre_tax_price'), blank=True, null=True)
    extra_documents = GenericRelation(Documents)
    current_price_change = models.FloatField(_('Current Price Change'), blank=True, null=True)
    parent_category_name = models.CharField(_('Parent Category Name'), blank=True, null=True, max_length=50)
    inventory_name = models.CharField(_('Inventory Name'), max_length=50, blank=True, null=True)
    thumbnail_url = models.CharField(_('Thumbnail Url'), blank=True, null=True, max_length=500)
    mobile_url = models.CharField(_('Mobile Url'), blank=True, null=True, max_length=500)
    nutrients = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    ethics_and_certification = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
    cf_payment_method = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
    mapped_items = JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')


class InventoryItemEdit(TimeStampFlagModelMixin, models.Model):
    """
    Custom Inventory Model Class
    """
    STATUS_CHOICES = (
        ('pending_for_approval', _('Pending For Approval')),
        ('approved', _('Approved')),
    )

    PRICING_POSITION_CHOICES = (
        ('Negotiable', _('Negotiable')),
        ('Firm', _('Firm')),
        ('Min Quantity', _('Min Quantity')),
        ('Offers Open', _('Offers Open')),
    )
    MARKETPLACE_STATUS_CHOICES = (
        ('Under Contract', _('Under Contract')),
        ('Sold', _('Sold')),
        ('Pending Sale', _('Pending Sale')),
        ('Available', _('Available')),
        ('In-Testing', _('In-Testing')),
        ('Processing', _('Processing')),
        ('Flowering', _('Flowering')),
        ('Vegging', _('Vegging')),
    )
    PAYMENT_TERMS_CHOICES = (
        ('60 Days', _('60 Days')),
        ('21 Days', _('21 Days')),
    )
    PAYMENT_METHOD_CHOICES = (
        ('Cash', _('Cash')),
        ('ACH', _('ACH')),
        ('Check', _('Check')),
        ('Bank Wire', _('Bank Wire')),
    )

    item = models.ForeignKey(Inventory, verbose_name=_('item'), related_name='edits', on_delete=models.CASCADE)
    item_data = JSONField(_('item_data'), null=True, blank=True, default=dict)
    name = models.CharField(_('Name'), blank=True, null=True, max_length=255)

    quantity_available = models.FloatField(_('Quantity Available'), blank=True, null=True,)
    batch_availability_date = models.DateField(_('Batch Availability Date'), auto_now=False, blank=True, null=True, default=None)

    farm_price = models.FloatField(_('Farm Price'), blank=True, null=True,)
    pricing_position = models.CharField(_('Pricing Position'), choices=PRICING_POSITION_CHOICES, blank=True, null=True, max_length=255)
    have_minimum_order_quantity = models.BooleanField(_('Minimum Order Quantity'), default=False)
    minimum_order_quantity = models.FloatField(_('Minimum Order Quantity(lbs)'), blank=True, null=True,)

    payment_terms = models.CharField(_('Payment Terms'), choices=PAYMENT_TERMS_CHOICES, blank=True, null=True, max_length=50)
    payment_method = ChoiceArrayField(models.CharField(_('Payment Method'), max_length=100, choices=PAYMENT_METHOD_CHOICES), blank=True, default=list)

    marketplace_status = models.CharField(_('Marketplace Status'), choices=MARKETPLACE_STATUS_CHOICES, max_length=225, blank=True, null=True,)

    extra_documents = GenericRelation(Documents)

    sku = models.CharField(_('SKU'), blank=True, null=True, max_length=255)
    cultivar_name = models.CharField(_('Cultivar Name'), blank=True, null=True, max_length=255)
    vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=255)
    zoho_item_id = models.CharField(_('Zoho Item ID'), blank=True, null=True, max_length=50)

    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default='pending_for_approval')
    created_by = JSONField(_('Created by'), null=True, blank=True, default=dict)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    approved_on = models.DateTimeField(_('Approved on'), auto_now=False, blank=True, null=True, default=None)

    def get_item_update_data(self):
        data = {
            'item_id': self.item.item_id,
            'inventory_name': self.item.inventory_name,
            'cf_date_available': self.batch_availability_date.strftime("%Y-%m-%d"),
            'cf_farm_price': str(self.farm_price),
            'cf_farm_price_2': self.farm_price,
            'cf_seller_position': self.pricing_position,
            'cf_payment_terms': self.payment_terms,
            'cf_payment_method': self.payment_method,
        }
        if self.marketplace_status:
            data['cf_status'] = self.marketplace_status
        # if self.have_minimum_order_quantity:
        #     data['cf_minimum_quantity'] = int(self.minimum_order_quantity)
        # else:
        #     data['cf_minimum_quantity'] = None
        return data

    def get_display_diff_data(self):
        data = {}
        data['farm_price'] = ('Farm Price', "${:,.2f}".format(self.item.cf_farm_price_2), "${:,.2f}".format(self.farm_price))
        data['pricing_position'] = ('Pricing Position', self.item.cf_seller_position, self.pricing_position)
        # data['minimum_order_quantity'] = (
        #     'Minimum Order Quantity',
        #     int(self.item.cf_minimum_quantity) if self.item.cf_minimum_quantity else None,
        #     int(self.minimum_order_quantity)  if self.have_minimum_order_quantity else None,
        # )
        data['payment_terms'] = ('Payment Terms', self.item.cf_payment_terms, self.payment_terms)
        data['payment_method'] = (
            'Payment Method',
            ', '.join(self.item.cf_payment_method) if self.item.cf_payment_method else None,
            ', '.join(self.payment_method) if self.payment_method else None,
        )
        data['batch_availability_date'] = (
            'Batch Availability Date',
                self.item.cf_date_available.strftime("%Y-%m-%d") if self.item.cf_date_available else None,
                self.batch_availability_date.strftime("%Y-%m-%d") if self.batch_availability_date else None,
        )
        if self.marketplace_status:
            data['marketplace_status'] = (
                'Marketplace Status',
                self.item.cf_status,
                self.marketplace_status,
            )
        return data

    def __str__(self):
        return "%s" % (self.item)

    class Meta:
        verbose_name = _('Item Edit Request')
        verbose_name_plural = _('Item Edit Requests')

class InventoryItemDelist(TimeStampFlagModelMixin, models.Model):
    """
    Custom Inventory Model Class
    """
    STATUS_CHOICES = (
        ('pending_for_approval', _('Pending For Approval')),
        ('approved', _('Approved')),
    )

    item = models.ForeignKey(Inventory, verbose_name=_('item'), related_name='deletion_requests', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), blank=True, null=True, max_length=255)
    item_data = JSONField(_('item_data'), null=True, blank=True, default=dict)

    sku = models.CharField(_('SKU'), blank=True, null=True, max_length=255)
    cultivar_name = models.CharField(_('Cultivar Name'), blank=True, null=True, max_length=255)
    vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=255)
    zoho_item_id = models.CharField(_('Zoho Item ID'), blank=True, null=True, max_length=50)

    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default='pending_for_approval')
    created_by = JSONField(_('Created by'), null=True, blank=True, default=dict)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    approved_on = models.DateTimeField(_('Approved on'), auto_now=False, blank=True, null=True, default=None)

    def __str__(self):
        return "%s" % (self.item)

    class Meta:
        verbose_name = _('Item Delist Request')
        verbose_name_plural = _('Item Delist Requests')



class InventoryItemQuantityAddition(TimeStampFlagModelMixin, models.Model):
    """
    Custom Inventory Model Class
    """
    STATUS_CHOICES = (
        ('pending_for_approval', _('Pending For Approval')),
        ('approved', _('Approved')),
    )

    item = models.ForeignKey(Inventory, verbose_name=_('item'), related_name='quantity_additions', on_delete=models.CASCADE)
    quantity = models.FloatField(_('Quantity'), blank=True, null=True,)

    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default='pending_for_approval')
    po_id = models.CharField(_('Purchase Order id'), blank=True, null=True, max_length=255)
    po_number = models.CharField(_('Purchase Order Number'), blank=True, null=True, max_length=255)
    created_by = JSONField(_('Created by'), null=True, blank=True, default=dict)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    approved_on = models.DateTimeField(_('Approved on'), auto_now=False, blank=True, null=True, default=None)

    def __str__(self):
        return "%s" % (self.item)

    class Meta:
        verbose_name = _('Quantity Addition')
        verbose_name_plural = _('Quantity Additions')



class CustomInventory(TimeStampFlagModelMixin, models.Model):
    """
    Custom Inventory Model Class
    """
    STATUS_CHOICES = (
        ('pending_for_approval', _('Pending For Approval')),
        ('approved', _('Approved')),
    )

    MARKETPLACE_STATUS_CHOICES = (
        ('Available', _('Available')),
        ('In-Testing', _('In-Testing')),
        ('Processing', _('Processing')),
        ('Flowering', _('Flowering')),
        ('Vegging', _('Vegging')),
        ('Rooting', _('Rooting')),
    )

    PRICING_POSITION_CHOICES = (
        ('Negotiable', _('Negotiable')),
        ('Firm', _('Firm')),
        ('Min Quantity', _('Min Quantity')),
        ('Offers Open', _('Offers Open')),
    )
    DAY_OF_WEEK = (
        ('monday', _('Monday')),
        ('tuesday', _('Tuesday')),
        ('wednesday', _('Wednesday')),
        ('thursday', _('Thursday')),
        ('friday', _('Friday')),
        ('saturday', _('Saturday')),
        ('sunday', _('Sunday')),
    )
    GRADE_ESTIMATE_CHOICES = (
        ('Smalls A', _('Smalls A')),
        ('Smalls B', _('Smalls B')),
        ('Smalls C', _('Smalls C')),
        ('Tops A', _('Tops A')),
        ('Tops AA', _('Tops AA')),
        ('Tops AAA', _('Tops AAA')),
        ('Tops B', _('Tops B')),
        ('Tops C', _('Tops C')),
        # ('Trim', _('Trim')),
    )

    CATEGORY_NAME_CHOICES = (
        ('Wholesale - Flower', _('Wholesale - Flower')),
        ('In the Field', _('In the Field')),
        ('Flower - Tops', _('Flower - Tops')),
        ('Flower - Bucked Untrimmed', _('Flower - Bucked Untrimmed')),
        ('Flower - Bucked Untrimmed - Seeded', _('Flower - Bucked Untrimmed - Seeded')),
        ('Flower - Bucked Untrimmed - Contaminated', _('Flower - Bucked Untrimmed - Contaminated')),
        ('Flower - Small', _('Flower - Small')),
        ('Trim', _('Trim')),
        ('Packaged Goods', _('Packaged Goods')),
        ('Isolates', _('Isolates')),
        ('Isolates - CBD', _('Isolates - CBD')),
        ('Isolates - THC', _('Isolates - THC')),
        ('Isolates - CBG', _('Isolates - CBG')),
        ('Isolates - CBN', _('Isolates - CBN')),
        ('Wholesale - Concentrates', _('Wholesale - Concentrates')),
        ('Crude Oil', _('Crude Oil')),
        ('Crude Oil - THC', _('Crude Oil - THC')),
        ('Crude Oil - CBD', _('Crude Oil - CBD')),
        ('Distillate Oil', _('Distillate Oil')),
        ('Distillate Oil - THC', _('Distillate Oil - THC')),
        ('Distillate Oil - CBD', _('Distillate Oil - CBD')),
        ('Shatter', _('Shatter')),
        ('Sauce', _('Sauce')),
        ('Crumble', _('Crumble')),
        ('Kief', _('Kief')),
        ('Lab Testing', _('Lab Testing')),
        ('Terpenes', _('Terpenes')),
        ('Terpenes - Cultivar Specific', _('Terpenes - Cultivar Specific')),
        ('Terpenes - Cultivar Blended', _('Terpenes - Cultivar Blended')),
        ('Services', _('Services')),
        ('QC', _('QC')),
        ('Transport', _('Transport')),
        ('Secure Cash Handling', _('Secure Cash Handling')),
        ('Clones', _('Clones')),
    )

    PAYMENT_TERMS_CHOICES = (
        ('60 Days', _('60 Days')),
        ('21 Days', _('21 Days')),
    )
    PAYMENT_METHOD_CHOICES = (
        ('Cash', _('Cash')),
        ('ACH', _('ACH')),
        ('Check', _('Check')),
        ('Bank Wire', _('Bank Wire')),
    )
    ZOHO_ORG_CHOICES = (
        ('efd', _('Thrive Society (EFD LLC)')),
        ('efl', _('Eco Farm Labs (EFL LLC)')),
        ('efn', _('Eco Farm Nursery (EFN LLC)')),
    )
    license_profile = models.ForeignKey('brand.LicenseProfile', verbose_name=_('License Profile'), related_name='custom_inventory', null=True, on_delete=models.SET_NULL)
    cultivar = models.ForeignKey(Cultivar, verbose_name=_('Cultivar'), related_name='custom_inventory', on_delete=models.PROTECT)
    # cultivar_name = models.CharField(_('Cultivar Name'), max_length=255,)
    # cultivation_type = models.CharField(_('Cultivation Type'), blank=True, null=True, max_length=255)
    category_name = models.CharField(_('Item Category Name'), choices=CATEGORY_NAME_CHOICES, null=True, max_length=225)
    marketplace_status = models.CharField(_('Marketplace Status'), choices=MARKETPLACE_STATUS_CHOICES, max_length=225, default='In-Testing')
    quantity_available = models.FloatField(_('Quantity Available'), blank=True, null=True,)
    harvest_date = models.DateField(_('Harvest/Manufacturing/Clone Date'), auto_now=False, blank=True, null=True, default=None)
    need_lab_testing_service = models.BooleanField(_('Need Lab Testing Service'),)
    batch_availability_date = models.DateField(_('Batch Availability Date'), auto_now=False, blank=True, null=True, default=None)
    grade_estimate = models.CharField(_('Grade Estimate'), choices=GRADE_ESTIMATE_CHOICES, max_length=255, blank=True, null=True)
    product_quality_notes = models.TextField(_('Product Quality Notes'), blank=True, null=True)
    extra_documents = GenericRelation(Documents)

    trim_used = models.FloatField(
        _('Trim Used (lbs)'),
        help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.',
        blank=True,
        null=True,
    )
    trim_used_verified = models.BooleanField(_('Trim Used Verified'), default=False)

    farm_ask_price = models.FloatField(_('Farm Ask Price'), blank=True, null=True,)
    pricing_position = models.CharField(_('Pricing Position'), choices=PRICING_POSITION_CHOICES, blank=True, null=True, max_length=255)
    have_minimum_order_quantity = models.BooleanField(_('Minimum Order Quantity'), default=False)
    minimum_order_quantity = models.FloatField(_('Minimum Order Quantity(lbs)'), blank=True, null=True,)

    transportation = models.CharField(_("Transportation / Sample Pickup"), max_length=255, blank=True, null=True)
    best_contact_Day_of_week = models.CharField(_("Best Contact Day Of Week"), max_length=50, choices=DAY_OF_WEEK, blank=True, null=True,)
    best_contact_time_from = models.TimeField(_('Best Contact Time From'), auto_now=False, blank=True, null=True, default=None)
    best_contact_time_to = models.TimeField(_('Best Contact Time To'), auto_now=False, blank=True, null=True, default=None)

    payment_terms = models.CharField(_('Payment Terms'), choices=PAYMENT_TERMS_CHOICES, blank=True, null=True, max_length=50)
    payment_method = ChoiceArrayField(models.CharField(_('Payment Method'), max_length=100, choices=PAYMENT_METHOD_CHOICES), default=list)

    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default='pending_for_approval')
    vendor_name = models.CharField(_('Vendor Name'), max_length=255)
    crm_vendor_id = models.CharField(_('CRM Vendor ID'), blank=True, null=True, max_length=255)
    zoho_item_id = models.CharField(_('Zoho Item ID'), blank=True, null=True, max_length=50)
    sku = models.CharField(_('SKU'), blank=True, null=True, max_length=255)
    po_id = models.CharField(_('Purchase Order id'), blank=True, null=True, max_length=255)
    po_number = models.CharField(_('Purchase Order Number'), blank=True, null=True, max_length=255)
    client_code = models.CharField(_('Client Code'), blank=True, null=True, max_length=255)
    procurement_rep = models.CharField(_('Procurement Rep'), blank=True, null=True, max_length=255)
    procurement_rep_name = models.CharField(_('Procurement Rep name'), blank=True, null=True, max_length=255)
    created_by = JSONField(_('Created by'), null=True, blank=True, default=dict)
    approved_by = JSONField(_('Approved by'), null=True, blank=True, default=dict)
    approved_on = models.DateTimeField(_('Approved on'), auto_now=False, blank=True, null=True, default=None)

    zoho_organization = models.CharField(_('Zoho Organization'), choices=ZOHO_ORG_CHOICES, null=True, max_length=100)

    class Meta:
        verbose_name = _('Vendor Inventory')
        verbose_name_plural = _('Vendor Inventory Items')


class ItemFeedback(TimeStampFlagModelMixin, models.Model):
    """
    Inventory item feedbacks by user.
    """
    user = models.ForeignKey(User, verbose_name=_('User'), related_name='user', on_delete=models.PROTECT)
    item = models.CharField(_('item_id'), blank=True, null=True, max_length=100)
    feedback = models.TextField(_('feedback'))
    estimate_number = models.CharField(_('Estimate Number'), blank=True, null=True, max_length=100)


class InTransitOrder(TimeStampFlagModelMixin, models.Model):
    """
    In-transit order details.
    """
    user = models.ForeignKey(User, verbose_name=_('User'), related_name='in_transit_order', on_delete=models.CASCADE,null=True,blank=True)
    profile_id = models.IntegerField(_('profile_id'), null=False, blank=False)
    order_data = JSONField(null=False, blank=False, default=dict)

    class Meta:
        unique_together = (('user', 'profile_id'), )
        verbose_name = _('In Transit order')
        verbose_name_plural = _('In Transit orders')
    

class PriceChange(TimeStampFlagModelMixin, models.Model):
    """
    Price change class.
    """
    item_id = models.CharField(_('item_id'), blank=True, null=True, max_length=100)
    price_array = ArrayField(JSONField(default=dict), blank=True, null=True)


class DailyInventoryAggrigatedSummary(models.Model):
    """
    Stores Inventory daily data.
    """
    date = models.DateField()
    total_thc_max = models.FloatField(_('Total THC(Max)'), blank=True, null=True, max_length=255)
    total_thc_min = models.FloatField(_('Total THC(Min)'), blank=True, null=True, max_length=255)
    batch_varities = models.IntegerField(_('Batches'), blank=True, null=True)
    average = models.FloatField(_('Average $/lb'), blank=True, null=True, max_length=255)
    total_value = models.FloatField(_('Total Value $'), blank=True, null=True, max_length=255)
    smalls_quantity = models.FloatField(_('Smalls(lbs)'), blank=True, null=True, max_length=255)
    tops_quantity = models.FloatField(_('Tops(lbs)'), blank=True, null=True, max_length=255)
    total_quantity = models.FloatField(_('Total(lbs)'), blank=True, null=True, max_length=255)
    trim_quantity =  models.FloatField(_('Trim quantity'), blank=True, null=True, max_length=255)
    average_thc = models.FloatField(_('Avg THC'), blank=True, null=True, max_length=255)
    
    def __str__(self):
        return "%s" % (self.date.strftime("%B %d,%Y"))

    class Meta:
        verbose_name = _('Daily Inventory Aggregated Summary')
        verbose_name_plural = _('Daily Inventory  Aggregated Summary')

        
class SummaryByProductCategory(models.Model):
    """
    Stores summary by parent_category_name.
    """ 
    PRODUCT_CATEGORY_CHOICES = (
        ('Wholesale - Flower', _('Wholesale - Flower')),
        ('Wholesale - Isolates', _('Wholesale - Isolates')),
        ('Wholesale - Terpenes', _('Wholesale - Terpenes')),
        ('Wholesale - Trim', _('Wholesale - Trim')),
        ('Wholesale - Concentrates', _('Wholesale - Concentrates')),
        ('Lab Testing', _('Lab Testing')),
        ('Services', _('Services')),
    )
    daily_aggrigated_summary = models.ForeignKey(DailyInventoryAggrigatedSummary,on_delete=models.CASCADE)
    product_category = models.CharField(_('PRODUCT/PARENT CATEGORY'), choices=PRODUCT_CATEGORY_CHOICES,max_length=255)    
    total_thc_max = models.FloatField(_('Total THC(Max)'), blank=True, null=True, max_length=255)
    total_thc_min = models.FloatField(_('Total THC(Min)'), blank=True, null=True, max_length=255)
    batch_varities = models.IntegerField(_('Batches'), blank=True, null=True)
    average = models.FloatField(_('Average $/lb'), blank=True, null=True, max_length=255)
    total_value = models.FloatField(_('Total Value $'), blank=True, null=True, max_length=255)
    smalls_quantity = models.FloatField(_('Smalls(lbs)'), blank=True, null=True, max_length=255)
    tops_quantity = models.FloatField(_('Tops(lbs)'), blank=True, null=True, max_length=255)
    total_quantity = models.FloatField(_('Total(lbs)'), blank=True, null=True, max_length=255)
    trim_quantity =  models.FloatField(_('Trim quantity'), blank=True, null=True, max_length=255)
    average_thc = models.FloatField(_('Avg THC'), blank=True, null=True, max_length=255)
    
    def __str__(self):
        return "%s" % (self.product_category)

    class Meta:
        unique_together = (('daily_aggrigated_summary', 'product_category'), )
        verbose_name = _('Summary by product category')

        
class County(models.Model):
    """
    Stores inventory county grown.
    """
    name = models.CharField(_('County Grown'), blank=True, null=True, max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Inventory County')
        verbose_name_plural = _('County Wise Summary')

class CountyDailySummary(models.Model):
    """
    Stores Inventory countiwise  daily data.
    """
    county = models.ForeignKey(County, verbose_name=_('County'),on_delete=models.CASCADE)
    date = models.DateField()
    total_thc_max = models.FloatField(_('Total THC(Max)'), blank=True, null=True, max_length=255)
    total_thc_min = models.FloatField(_('Total THC(Min)'), blank=True, null=True, max_length=255)
    batch_varities = models.IntegerField(_('Batches'), blank=True, null=True)
    average = models.FloatField(_('Average $/lb'), blank=True, null=True, max_length=255)
    total_value = models.FloatField(_('Total Value $'), blank=True, null=True, max_length=255)
    smalls_quantity = models.FloatField(_('Smalls(lbs)'), blank=True, null=True, max_length=255)
    tops_quantity = models.FloatField(_('Tops(lbs)'), blank=True, null=True, max_length=255)
    total_quantity = models.FloatField(_('Total(lbs)'), blank=True, null=True, max_length=255)
    trim_quantity =  models.FloatField(_('Trim quantity'), blank=True, null=True, max_length=255)
    average_thc = models.FloatField(_('Avg THC'), blank=True, null=True, max_length=255)
    
    def __str__(self):
        return "%s" % (self.date.strftime("%B %d,%Y"))

    class Meta:
        unique_together = (('date', 'county'), )
        verbose_name = _('Daily County Summary')
        verbose_name_plural = _('Daily County Summary')


class Summary(TimeStampFlagModelMixin, models.Model):
    """
    summary model.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    date = models.DateField(blank=True, null=True)
    total_thc_max = models.FloatField(_('Total THC(Max)'), blank=True, null=True, max_length=255)
    total_thc_min = models.FloatField(_('Total THC(Min)'), blank=True, null=True, max_length=255)
    batch_varities = models.IntegerField(_('Batches'), blank=True, null=True)
    average = models.FloatField(_('Average $/lb'), blank=True, null=True, max_length=255)
    total_value = models.FloatField(_('Total Value $'), blank=True, null=True, max_length=255)
    smalls_quantity = models.FloatField(_('Smalls(lbs)'), blank=True, null=True, max_length=255)
    tops_quantity = models.FloatField(_('Tops(lbs)'), blank=True, null=True, max_length=255)
    total_quantity = models.FloatField(_('Total(lbs)'), blank=True, null=True, max_length=255)
    trim_quantity =  models.FloatField(_('Trim quantity'), blank=True, null=True, max_length=255)
    average_thc = models.FloatField(_('Avg THC'), blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = _('Summary')
        verbose_name_plural = _('Summary')

        
class Vendor(models.Model):
    """
    Separately stored vendor name & code  as in future we may need APIs independently.
    """
    vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True,max_length=255)
    cf_client_code = models.CharField(_('Client Code'), blank=True, null=True, max_length=50)
    
    def __str__(self):
        return self.cf_client_code or ''

    class Meta:
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendor Wise Summary')
   
class VendorDailySummary(models.Model):
    """
    Daily summary by vendor.
    """
    vendor = models.ForeignKey(Vendor,on_delete=models.CASCADE)
    summary = GenericRelation(Summary)

    class Meta:
        verbose_name = _('Vendor Daily Summary')
        verbose_name_plural = _('Vendor Daily Summary')
    

