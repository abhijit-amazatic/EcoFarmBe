"""
Inventory Model
"""
from datetime import date
from decimal import Decimal
from operator import attrgetter
from django import forms
from django.core.validators import MinValueValidator
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.contenttypes.fields import (GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import (cached_property)
from django.contrib.postgres.fields import (ArrayField, JSONField,)

from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from core.mixins.models import (TimeStampFlagModelMixin, )
from core.db.models import (PercentField, PositiveDecimalField)
from user.models import (User, )
from .fields import (ChoiceArrayField,)
from .data import (
    CG,
    CATEGORY_CANNABINOID_TYPE_MAP,
    ITEM_CATEGORY_UNIT_MAP
)

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
    S3_url = models.CharField(_('Box Url'), blank=True, null=True, max_length=500)
    s3_thumbnail_url = models.CharField(_('Thumbnail Url'), blank=True, null=True, max_length=500)
    S3_mobile_url = models.CharField(_('Mobile Url'), blank=True, null=True, max_length=500)
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
    manufacturer = models.CharField(_('Manufacturer'), blank=True, null=True, max_length=100)
    category_name = models.CharField(_('Category Name'), max_length=50)
    category_id = models.CharField(_('Category ID'), blank=True, null=True, max_length=50)
    vendor_id = models.CharField(_('Vendor ID'), blank=True, null=True, max_length=50)
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
    cf_vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=255)
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

    cf_biomass = models.CharField(_('Biomass Type'), blank=True, null=True, max_length=100)
    cf_trim_qty_lbs = models.FloatField(_('Trim Quantity Used (lbs)'), blank=True, null=True)
    cf_batch_qty_g = models.FloatField(_('Total Batch Output (grams)'), null=True, blank=True)
    cf_raw_material_input_g = models.DecimalField(_('Biomass Input (grams)'), max_digits=16, decimal_places=6, blank=True, null=True)
    cf_mscp = models.DecimalField(_('MCSP fee'), max_digits=16, decimal_places=6, blank=True, null=True)
    cf_cultivation_tax = models.DecimalField(_('Cultivation Tax'), max_digits=16, decimal_places=6, blank=True, null=True)

    package_details = JSONField(blank=True, null=True, default=dict)
    documents = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    batches = ArrayField(JSONField(default=dict), blank=True, null=True)
    pre_tax_price = models.FloatField(_('pre_tax_price'), blank=True, null=True)
    current_price_change = models.FloatField(_('Current Price Change'), blank=True, null=True)
    parent_category_name = models.CharField(_('Parent Category Name'), blank=True, null=True, max_length=50)
    inventory_name = models.CharField(_('Inventory Name'), max_length=50, blank=True, null=True)
    thumbnail_url = models.CharField(_('Thumbnail Url'), blank=True, null=True, max_length=500)
    mobile_url = models.CharField(_('Mobile Url'), blank=True, null=True, max_length=500)
    nutrients = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    ethics_and_certification = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
    cf_payment_method = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
    mapped_items = JSONField(blank=True, null=True, default=dict)
    client_id = models.PositiveIntegerField(blank=True, null=True)
    item_qr_code_url = models.CharField(_('QR Code-Box URL'), blank=True, null=True, max_length=500)
    qr_code_box_id = models.CharField(_('QR Code-Box ID'), blank=True, null=True, max_length=255)
    qr_box_direct_url = models.CharField(_('QR direct Box URL'), blank=True, null=True, max_length=500)
    cf_featured = models.BooleanField(_('Featured'), default=False)
    extra_documents = GenericRelation(Documents)
    

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
    BIOMASS_TYPE_CHOICES = (
        ('Unknown',  _('Unknown')),
        ('Dried Flower', _('Dried Flower')),
        ('Dried Leaf', _('Dried Leaf')),
        ('Fresh Plant', _('Fresh Plant')),
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
    item_data = JSONField(_('item_data'), null=True, blank=True, default=dict, encoder=DjangoJSONEncoder)
    name = models.CharField(_('Name'), blank=True, null=True, max_length=255)

    quantity_available = models.FloatField(_('Quantity Available'), blank=True, null=True,)
    batch_availability_date = models.DateField(_('Batch Availability Date'), auto_now=False, blank=True, null=True, default=None)

    farm_price = models.FloatField(_('Farm Price'), blank=True, null=True,)
    pricing_position = models.CharField(_('Pricing Position'), choices=PRICING_POSITION_CHOICES, blank=True, null=True, max_length=255)
    have_minimum_order_quantity = models.BooleanField(_('Minimum Order Quantity'), default=False)
    minimum_order_quantity = models.FloatField(_('Minimum Order Quantity(lbs)'), blank=True, null=True,)

    biomass_type = models.CharField(_('Biomass Type'), choices=BIOMASS_TYPE_CHOICES, blank=True, null=True, max_length=50)
    biomass_input_g = PositiveDecimalField(
        _('Raw Material Input (grams)'),
        decimal_places=6,
        max_digits=16,
        help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.',
        blank=True,
        null=True,
    )
    total_batch_quantity = PositiveDecimalField(
        _('Total Batch Output'),
        decimal_places=6,
        max_digits=16,
        help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.',
        blank=True,
        null=True,
    )
    mcsp_fee = PositiveDecimalField(_('MCSP Fee'), decimal_places=6, max_digits=16, blank=True, null=True)
    cultivation_tax = PositiveDecimalField(_('Cultivation Tax'), decimal_places=6, max_digits=16, blank=True, null=True)

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

    UPDATE_FIELDS = {
        'farm_price':              'cf_farm_price_2',
        # 'minimum_order_quantity':  'cf_minimum_quantity',
        'pricing_position':        'cf_seller_position',
        'biomass_type':            'cf_biomass',
        'biomass_input_g':         'cf_raw_material_input_g',
        'total_batch_quantity':    'cf_batch_qty_g',
        'mcsp_fee':                'cf_mscp',
        'cultivation_tax':         'cf_cultivation_tax',
        'payment_terms':           'cf_payment_terms',
        'payment_method':          'cf_payment_method',
        'batch_availability_date': 'cf_date_available',
        'marketplace_status':      'cf_status',
    }

    @cached_property
    def filds_verbose_name(self):
        fields = self.__class__._meta.fields
        return {f.name: f.verbose_name or f.name.title() for f in fields}

    def get_item_update_data(self):
        data = { v: getattr(self, k) for k, v in self.UPDATE_FIELDS.items()}
        data['item_id'] = self.item.item_id
        return data


    def get_display_diff_data(self):
        field_formats = {
            'farm_price': lambda v: f"${v:,.2f}" if v is not None else None,
            'mcsp_fee': lambda v: f"${Decimal(v):,.2f}" if v is not None else v,
            'cultivation_tax': lambda v: f"${Decimal(v):,.2f}" if v is not None else v,
            'batch_availability_date': lambda v: v.strftime("%Y-%m-%d") if isinstance(v, date) else v,
            'minimum_order_quantity': lambda v: int(v) if v else None,
            'payment_method': lambda v: ', '.join(v) if v else None,
        }
        data = {
            k: (self.filds_verbose_name[k], self.item_data[v], getattr(self, k))
            for k, v in self.UPDATE_FIELDS.items()
        }
        data.update({
            k : (data[k][0], f(data[k][1]), f(data[k][2]))
            for k, f in field_formats.items() if k in data
        })
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
    item_data = JSONField(_('item_data'), null=True, blank=True, default=dict, encoder=DjangoJSONEncoder)

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
    CATEGORY_NAME_CHOICES = (
        ('Flower - Tops', _('Flower - Tops')),
        ('Flower - Small', _('Flower - Small')),
        ('Trim', _('Trim')),
        ('Isolates - CBD', _('Isolates - CBD')),
        ('Isolates - THC', _('Isolates - THC')),
        ('Isolates - CBG', _('Isolates - CBG')),
        ('Isolates - CBN', _('Isolates - CBN')),
        ('Crude Oil - THC', _('Crude Oil - THC')),
        ('Crude Oil - CBD', _('Crude Oil - CBD')),
        ('Distillate Oil - THC', _('Distillate Oil - THC')),
        ('Distillate Oil - CBD', _('Distillate Oil - CBD')),
        ('Hash', _('Hash')),
        ('Shatter', _('Shatter')),
        ('Sauce', _('Sauce')),
        ('Crumble', _('Crumble')),
        ('Kief', _('Kief')),
        ('Badder', _('Badder')),
        ('Live Resin', _('Live Resin')),
        ('Rosin', _('Rosin')),
        ('HTE', _('HTE')),
        ('Liquid Diamond Sauce', _('Liquid Diamond Sauce')),
        ('Terpenes - Cultivar Specific', _('Terpenes - Cultivar Specific')),
        ('Terpenes - Cultivar Blended', _('Terpenes - Cultivar Blended')),
        ('Clones', _('Clones')),
    )
    MARKETPLACE_STATUS_CHOICES = (
        ('Available', _('Available')),
        ('In-Testing', _('In-Testing')),
        ('Processing', _('Processing')),
        ('Flowering', _('Flowering')),
        ('Vegging', _('Vegging')),
        ('Cut to Order', _('Cut to Order')),
        ('Rooting', _('Rooting')),
    )

    CULTIVAR_TYPE_CHOICES = (
        ('Sativa', _('Sativa')),
        ('Indica', _('Indica')),
        ('Hybrid', _('Hybrid')),
    )
    CULTIVATION_TYPE_CHOICES = (
        ('Indoor',  _('Indoor')),
        ('Outdoor', _('Outdoor')),
        ('Mixed-Light', _('Mixed-Light')),
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

    PAYMENT_TERMS_CHOICES = (
        ('60 Days', _('60 Days')),
        ('21 Days', _('21 Days')),
        ('COD', _('COD')),
    )
    PAYMENT_METHOD_CHOICES = (
        ('Cash', _('Cash')),
        ('ACH', _('ACH')),
        ('Check', _('Check')),
        ('Bank Wire', _('Bank Wire')),
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

    STATUS_CHOICES = (
        ('pending_for_approval', _('Pending For Approval')),
        ('approved', _('Approved')),
    )
    ZOHO_ORG_CHOICES = (
        ('efd', _('Thrive Society (EFD LLC)')),
        ('efl', _('Eco Farm Labs (EFL LLC)')),
        ('efn', _('Eco Farm Nursery (EFN LLC)')),
    )
    BIOMASS_TYPE_CHOICES = (
        ('Unknown',  _('Unknown')),
        ('Dried Flower', _('Dried Flower')),
        ('Dried Leaf', _('Dried Leaf')),
        ('Fresh Plant', _('Fresh Plant')),
    )

    license_profile = models.ForeignKey('brand.LicenseProfile', verbose_name=_('License Profile'), related_name='custom_inventory', null=True, on_delete=models.SET_NULL)
    cultivar = models.ForeignKey(Cultivar, verbose_name=_('Cultivar'), related_name='custom_inventory', on_delete=models.SET_NULL, blank=True, null=True,)
 
    cultivar_name = models.CharField(_('Cultivar Name'), blank=True, null=True, max_length=255,)
    cultivar_type = models.CharField(_('Cultivar Type'), choices=CULTIVAR_TYPE_CHOICES, blank=True, null=True, max_length=255, )
    cultivar_crm_id = models.CharField(_('Cultivar CRM ID'), blank=True, null=True, max_length=255)
    mfg_batch_id = models.CharField(_('Batch ID'), blank=True, null=True, max_length=255)
 
    cultivation_type = models.CharField(_('Cultivation Type'), choices=CULTIVATION_TYPE_CHOICES, blank=True, null=True, max_length=255)
    category_name = models.CharField(_('Item Category Name'), choices=CATEGORY_NAME_CHOICES, max_length=225)
    marketplace_status = models.CharField(_('Marketplace Status'), choices=MARKETPLACE_STATUS_CHOICES, max_length=225, default='In-Testing')

    quantity_available = models.FloatField(_('Quantity Available'))
    biomass_type = models.CharField(_('Biomass Type'), choices=BIOMASS_TYPE_CHOICES, blank=True, null=True, max_length=50)
    biomass_input_g = PositiveDecimalField(
        _('Raw Material Input (grams)'),
        decimal_places=6,
        max_digits=16,
        help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.',
        blank=True,
        null=True,
    )
    total_batch_quantity = PositiveDecimalField(
        _('Total Batch Output'),
        decimal_places=6,
        max_digits=16,
        help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.',
        blank=True,
        null=True,
    )
    biomass_used_verified = models.BooleanField(_('Biomass Used Verified'), default=False)
    cultivation_tax = PositiveDecimalField(_('Cultivation Tax'), decimal_places=6, max_digits=16, blank=True, null=True)
    mcsp_fee = PositiveDecimalField(_('MCSP Fee'), decimal_places=6, max_digits=16, blank=True, null=True)


    harvest_date = models.DateField(_('Harvest Date'), auto_now=False, blank=True, null=True, default=None)
    manufacturing_date = models.DateField(_('Manufacturing Date'), auto_now=False, blank=True, null=True, default=None)
    cannabinoid_percentage = PercentField(_("Cannabinoid Percentage"), blank=True, null=True)
    clone_date = models.DateField(_('Clone Date'), auto_now=False, blank=True, null=True, default=None)
    rooting_days = models.PositiveIntegerField(_('Rooting Days'), blank=True, null=True,)
    batch_availability_date = models.DateField(_('Batch Availability Date'), auto_now=False, blank=True, null=True, default=None)

    need_lab_testing_service = models.BooleanField(_('Need Lab Testing Service'),)
    grade_estimate = models.CharField(_('Grade Estimate'), choices=GRADE_ESTIMATE_CHOICES, max_length=255, blank=True, null=True)
    product_quality_notes = models.TextField(_('Product Quality Notes'), blank=True, null=True)

    clone_size = models.PositiveIntegerField(_('Clone Size (inch)'), blank=True, null=True,)

    farm_ask_price = models.DecimalField(_("Farm Ask Price"), max_digits=16, decimal_places=6)
    pricing_position = models.CharField(_('Pricing Position'), choices=PRICING_POSITION_CHOICES, blank=True, null=True, max_length=255)

    # have_minimum_order_quantity = models.BooleanField(_('Minimum Order Quantity'), default=False)
    # minimum_order_quantity = models.FloatField(_('Minimum Order Quantity(lbs)'), blank=True, null=True,)

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

    extra_documents = GenericRelation(Documents)

    @property
    def get_cultivar_name(self):
        if self.cultivar:
            return self.cultivar.cultivar_name or self.cultivar_name or ''
        return self.cultivar_name or ''

    @property
    def get_cultivar_type(self):
        if self.cultivar:
            return self.cultivar.cultivar_type or self.cultivar_type or ''
        return self.cultivar_type or ''

    @property
    def category_group(self):
        return CG.get(self.category_name, '')

    @property
    def unit(self):
        return ITEM_CATEGORY_UNIT_MAP.get(self.category_group, '')

    @property
    def cannabinoid_type(self):
        return CATEGORY_CANNABINOID_TYPE_MAP.get(self.category_name, '')

    @property
    def cannabinoid_percentage_str(self):
        if self.cannabinoid_percentage:
            percent_val = round(self.cannabinoid_percentage, 2)
            return str(percent_val) if percent_val%1 else str(int(percent_val))
        return ''

    @property
    def cannabinoid_percentage_formatted(self):
        if self.cannabinoid_percentage_str:
            return self.cannabinoid_percentage_str.strip()+'%'
        return ''

    @property
    def mcsp_fee_formatted(self):
        return f'${self.mcsp_fee:,.2f}' if isinstance(self.mcsp_fee, Decimal) else ''

    @property
    def cultivation_tax_formatted(self):
        return f'${self.cultivation_tax:,.2f}' if isinstance(self.cultivation_tax, Decimal) else ''

    @property
    def farm_ask_price_formatted(self):
        return f'${self.farm_ask_price:,.2f}' if isinstance(self.farm_ask_price, Decimal) else ''

    @property
    def need_lab_testing_service_formatted(self):
        return 'Yes' if self.need_lab_testing_service else 'No'

    @property
    def biomass_input_g_formatted(self):
        if self.biomass_input_g is not None:
            return f"{self.biomass_input_g.normalize():f}"
        return ''

    @property
    def total_batch_quantity_formatted(self):
        if self.total_batch_quantity is not None:
            return f"{self.total_batch_quantity.normalize():f}"
        return ''

    @property
    def item_name(self):
        category_group = CG.get(self.category_name)
        name = ''
        if category_group in ('Isolates', 'Distillates',):
            if category_group == 'Isolates':
                name += 'Isolate'
            elif category_group == 'Distillates':
                name += 'Distillate'
            if name and self.cannabinoid_percentage_formatted:
                name += f' {self.cannabinoid_percentage_formatted}'
            if self.cannabinoid_type:
                name = f'{self.cannabinoid_type} {name}'
            return name
        elif category_group in ('Concentrates',):
            if self.category_name in ('Crude Oil - THC','Crude Oil - CBD'):
                name = f'{self.get_cultivar_name} {self.cannabinoid_type} Crude Oil'
            else:
                name = f'{self.get_cultivar_name} {self.category_name}'
        elif category_group in ('Flowers', 'Trims', 'Kief', 'Terpenes', 'Clones',):
            name = self.get_cultivar_name

        return name

    @property
    def pick_contact_time_formatted(self):
        contact_time = []
        if self.best_contact_time_from:
            contact_time.append(self.best_contact_time_from.strftime("%I:%M %p"))
        if self.best_contact_time_to:
            contact_time.append(self.best_contact_time_to.strftime("%I:%M %p"))

        pick_contact_time = []
        if self.best_contact_Day_of_week:
            pick_contact_time.append(self.best_contact_Day_of_week.title())
        if contact_time:
            pick_contact_time.append(' - '.join(contact_time))
        if pick_contact_time:
            return ' '.join(pick_contact_time)
        return ''

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
    profile_id = models.IntegerField(_('profile_id'), null=False, blank=False, unique=True)
    order_data = JSONField(null=False, blank=False, default=dict)

    class Meta:
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
    

