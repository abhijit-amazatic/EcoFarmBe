"""
Inventory Model
"""
from django.contrib.contenttypes.fields import (GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from core.mixins.models import (TimeStampFlagModelMixin, )
from user.models import (User, )


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
    cf_cultivar_type = models.CharField(_('Cultivar Type'), blank=True, null=True, max_length=50)
    cf_procurement_rep = models.CharField(_('Procurement Rep'), blank=True, null=True, max_length=50)
    cf_cfi_published = models.BooleanField(_('CFI_Published'), blank=True, null=True)
    cf_ifp_farm = models.BooleanField(_('IFP_Farm'), blank=True, null=True)
    cf_vendor_name = models.CharField(_('Vendor Name'), blank=True, null=True, max_length=50)
    county_grown = models.CharField(_('County Grown'), blank=True, null=True, max_length=50)
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
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
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
    cf_minimum_quantity = models.FloatField(_('Minimum Quantity'), blank=True, null=True)
    cf_available_date = models.DateField(auto_now=False, blank=True, null=True, default=None)
    package_details = JSONField(blank=True, null=True, default=dict)
    documents = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    batches = ArrayField(JSONField(default=dict), blank=True, null=True)
    pre_tax_price = models.FloatField(_('pre_tax_price'), blank=True, null=True)
    extra_documents = GenericRelation(Documents)
    current_price_change = models.FloatField(_('Current Price Change'), blank=True, null=True)
    parent_category_name = models.CharField(_('Parent Category Name'), blank=True, null=True, max_length=50)
    inventory_name = models.CharField(_('Inventory Name'), max_length=50, blank=True, null=True)
    thumbnail_url = models.CharField(_('Thumbnail Url'), blank=True, null=True, max_length=500)
    nutrients = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    ethics_and_certification = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)

    def __str__(self):
        return self.name


class CustomInventory(TimeStampFlagModelMixin, models.Model):
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
    DAY_OF_WEEK = (
        ('monday', _('Monday')),
        ('tuesday', _('Tuesday')),
        ('wednesday', _('Wednesday')),
        ('thursday', _('Thursday')),
        ('friday', _('Friday')),
        ('saturday', _('Saturday')),
        ('sunday', _('Sunday')),
    )
    cultivar = models.ForeignKey(Cultivar, verbose_name=_('Cultivar'),related_name='custom_inventory', on_delete=models.PROTECT)
    # cultivar_name = models.CharField(_('Cultivar Name'), max_length=255,)
    # cultivation_type = models.CharField(_('Cultivation Type'), blank=True, null=True, max_length=255)
    category_name = models.CharField(_('Item Category Name'), blank=True, null=True, max_length=225)
    category_id = models.CharField(_('Category ID'), blank=True, null=True, max_length=50)
    quantity_available = models.DecimalField(_('Quantity Available'), blank=True, null=True, max_digits=4, decimal_places=2)
    harvest_date = models.DateField(_('Harvest Date'), auto_now=False, blank=True, null=True, default=None)
    need_lab_testing_service = models.BooleanField(_('Need Lab Testing Service'),)
    batch_availability_date = models.DateField(_('Batch Availability Date'), auto_now=False, blank=True, null=True, default=None)
    grade_estimate = models.CharField(_('Grade Estimate'), max_length=255, blank=True, null=True)
    product_quality_notes = models.TextField(_('Product Quality Notes'), blank=True, null=True)
    extra_documents = GenericRelation(Documents)

    farm_ask_price = models.CharField(_('Farm Ask Price'), blank=True, null=True, max_length=100)
    pricing_position = models.CharField(_('Pricing Position'), choices=PRICING_POSITION_CHOICES, blank=True, null=True, max_length=255)
    have_minimum_order_quantity = models.BooleanField(_('Minimum Order Quantity'), default=False)
    minimum_order_quantity = models.DecimalField(_('Minimum Order Quantity(lbs)'), blank=True, null=True, max_digits=4, decimal_places=2)

    transportation = models.CharField(_("Transportation / Sample Pickup"), max_length=255, blank=True, null=True)
    best_contact_Day_of_week = models.CharField(_("Best Contact Day Of Week"), max_length=50, choices=DAY_OF_WEEK, blank=True, null=True,)
    best_contact_time_from = models.TimeField(_('Best Contact Time From'), auto_now=False, blank=True, null=True, default=None)
    best_contact_time_to = models.TimeField(_('Best Contact Time To'), auto_now=False, blank=True, null=True, default=None)

    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default='pending_for_approval')
    vendor_name = models.CharField(_('Vendor Name'), max_length=255)


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
    user = models.ForeignKey(User, verbose_name=_('User'), related_name='in_transit_order', on_delete=models.CASCADE)
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
