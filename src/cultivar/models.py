from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)

class Cultivar(models.Model):
    """
    Model for cultivar.
    """
    STATUS_CHOICES = (
        ('pending_for_approval', _('Pending For Approval')),
        ('approved', _('Approved')),
    )
    CULTIVAR_TYPE_CHOICES = (
        ('Sativa', _('Sativa')),
        ('Indica', _('Indica')),
        ('Hybrid', _('Hybrid')),
        ('Hybrid - Indica Dominant', _('Hybrid - Indica Dominant')),
        ('Hybrid - Sativa Dominant', _('Hybrid - Sativa Dominant')),
    )

    cultivar_crm_id = models.CharField(_('Cultivar ID'), blank=True, null=True, max_length=255)
    cultivar_name = models.CharField(_('Cultivar Name'), blank=True, null=True, max_length=255)
    cultivar_type = models.CharField(_('Cultivar Type'), choices=CULTIVAR_TYPE_CHOICES, blank=True, null=True, max_length=50)
    description = models.TextField(_('Description'), blank=True, null=True)
    thc_range = models.FloatField(_('THC'), blank=True, null=True)
    cbd_range = models.FloatField(_('CBD'), blank=True, null=True)
    cbg_range = models.FloatField(_('CBG'), blank=True, null=True)
    thcv_range = models.FloatField(_('THCv'), blank=True, null=True)
    thc_range_high = models.FloatField(_('THC HIGH'), blank=True, null=True)
    cbd_range_high = models.FloatField(_('CBD HIGH'), blank=True, null=True)
    cbg_range_high = models.FloatField(_('CBG HIGH'), blank=True, null=True)
    thcv_range_high = models.FloatField(_('THCv HIGH'), blank=True, null=True)
    thc_range_low = models.FloatField(_('THC LOW'), blank=True, null=True)
    cbd_range_low = models.FloatField(_('CBD LOW'), blank=True, null=True)
    cbg_range_low = models.FloatField(_('CBG LOW'), blank=True, null=True)
    thcv_range_low = models.FloatField(_('THCv LOW'), blank=True, null=True)
    flavor = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    effect = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    terpenes_primary = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    terpenes_secondary = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    parent_1 = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    parent_2 = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    cultivar_image = models.URLField(_('Image'), blank=True, null=True, max_length=255)
    lab_test_crm_id = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    modified_by = models.CharField(_('Modified By'), blank=True, null=True, max_length=255)
    created_by = models.CharField(_('Created By'), blank=True, null=True, max_length=255)
    create_time = models.DateTimeField(auto_now=False, blank=True, null=True)
    modify_time = models.DateTimeField(auto_now=False, blank=True, null=True)
    status = models.CharField(_('Status'), choices=STATUS_CHOICES, max_length=255, default='pending_for_approval')

    def __str__(self):
        if self.cultivar_name:
            return f'{self.cultivar_name} ({self.id})'
        else:
            return super().__str__()