from django.db import models
from django.utils.translation import ugettext_lazy as _
from core.mixins.models import (TimeStampFlagModelMixin, )
from django.contrib.postgres.fields import (ArrayField, JSONField,)


class Estimate(TimeStampFlagModelMixin, models.Model):
    """
    Estimate model.
    """
    EFD = 'EFD'
    EFL = 'EFL'
    EFN = 'EFN'
    ORGANIZATION_CHOICES = (
        (EFD, 'efd'),
        (EFL, 'efl'),
        (EFN, 'efn'),
    )
    
    DRAFT = 'draft' # Order is only in db.
    SENT = 'sent' # Order is sent to user for sign after creating in zoho.
    SIGNED = 'signed' # Order is signed by user.
    PROGRESS_CHOICES = (
        (DRAFT, 'draft'),
        (SENT, 'sent'),
        (SIGNED, 'signed')
    )
    
    estimate_id = models.CharField(_('Estimate ID'), blank=True, null=True, max_length=50)
    estimate_number = models.CharField(_('Estimate Number'), blank=True, null=True, max_length=255)
    organization = models.CharField(_('Organization'), choices=ORGANIZATION_CHOICES, default='efd', max_length=50)
    estimate_date = models.DateField(auto_now=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    status = models.CharField(_('Status'), default='draft', max_length=255)
    customer_id = models.CharField(_('Customer ID'), blank=True, null=True, max_length=255)
    customer_name = models.CharField(_('Customer Name'), max_length=255)
    currency_id = models.CharField(_('Currency ID'), blank=True, null=True, max_length=50)
    currency_code = models.CharField(_('Currency Code'), blank=True, null=True, max_length=50)
    discount = models.FloatField(_('Discount'), default=0.0)
    is_discount_before_tax = models.BooleanField(_('Is Discount Before Tax'), default=False)
    is_inclusive_tax = models.BooleanField(_('Is Inclusive Tax'), default=False)
    estimate_url = models.URLField(_('Estimate URL'), blank=True, null=True, max_length=255)
    shipping_charge = models.FloatField(_('Shipping Charge'), default=0.0)
    roundoff_value = models.FloatField(_('RoundOff Value'), default=0.0)
    sub_total = models.FloatField(_('Subtotal'), blank=True, null=True, )
    sub_total_inclusive_of_tax = models.FloatField(_('Subtotal'), blank=True, null=True)
    total = models.FloatField(_('Total'))
    tax_total = models.FloatField(_('Tax Total'), blank=True, null=True)
    billing_address = models.TextField(_('Billing Address'), blank=True, null=True)
    shipping_address = models.TextField(_('Shipping Address'), blank=True, null=True)
    notes = models.TextField(_('Notes'), blank=True, null=True)
    terms = models.TextField(_('Terms'), blank=True, null=True)
    custom_fields = ArrayField(JSONField(default=dict), blank=True, null=True)
    contact_persons_details = JSONField(default=dict)
    salesperson_id = models.CharField(_('Salesperson ID'), blank=True, null=True, max_length=255)
    salesperson_name = models.CharField(_('Salesperson Name'), max_length=255)
    payment_options = models.CharField(_('Payment Options'), max_length=255)
    request_id = models.CharField(_('Request ID'), blank=True, null=True, max_length=255)
    db_status = models.CharField(_('Progress'), choices=PROGRESS_CHOICES, default='draft', max_length=50)

    class Meta:
        verbose_name = _("estimate")
        verbose_name_plural = _("estimates")

    def __str__(self):
        return str(self.customer_name)
    
class LineItem(TimeStampFlagModelMixin, models.Model):
    """
    Line Item model.
    """
    estimate = models.ForeignKey(Estimate, verbose_name=_('Estimate'),
                                 related_name='estimate', on_delete=models.CASCADE)
    item_id = models.CharField(_('item_id'), max_length=255)
    sku = models.CharField(_('SKU'), max_length=255)
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True, max_length=255)
    item_order = models.CharField(_('Item Order'), max_length=255)
    rate = models.FloatField(_('Rate'))
    quantity = models.FloatField(_('Quantity'))
    unit = models.CharField(_('Unit'), max_length=50)
    discount_amount = models.FloatField(_('Discount Amount'), default=0.0)
    discount = models.CharField(_('Discount'), blank=True, null=True, max_length=255)
    tax_id = models.CharField(_('Tax ID'), blank=True, null=True, max_length=255)
    tax_name = models.CharField(_('Tax Name'), blank=True, null=True, max_length=255)
    tax_type = models.CharField(_('Tax Type'), blank=True, null=True, max_length=255)
    tax_percentage = models.FloatField(_('Tax Percentage'), blank=True, null=True)
    item_total = models.FloatField(_('Total'))
    item_custom_fields = ArrayField(JSONField(default=dict), blank=True, null=True)

    class Meta:
        verbose_name = _("lineitem")
        verbose_name_plural = _("lineitems")

    def __str__(self):
        return self.name
    
# class Offers(TimeStampFlagModelMixin, models.Model):
#     """
#     Offer table.
#     """
#     estimate = models.ForeignKey(Estimate, verbose_name=_('Estimate'),
#                                  related_name='estimate', on_delete=models.CASCADE)
#     seller
#     buyer
#     line_item
#     offer price
