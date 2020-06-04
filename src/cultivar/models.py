from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField, JSONField,)

class Cultivar(models.Model):
    """
    Model for cultivar.
    """
    cultivar_crm_id = models.CharField(_('Cultivar ID'), blank=True, null=True, max_length=255)
    cultivar_name = models.CharField(_('Cultivar Name'), blank=True, null=True, max_length=255)
    cultivar_type = models.CharField(_('Cultivar Type'), blank=True, null=True, max_length=50)
    description = models.TextField(_('Description'), blank=True, null=True)
    thc_range = models.FloatField(_('THC'), blank=True, null=True)
    cbd_range = models.FloatField(_('CBD'), blank=True, null=True)
    cbg_range = models.FloatField(_('CBG'), blank=True, null=True)
    thcv_range = models.FloatField(_('THCv'), blank=True, null=True)
    flavor = models.CharField(_('Flavor'), blank=True, null=True, max_length=255)
    effect = models.CharField(_('Effect'), blank=True, null=True, max_length=255)
    terpenes_primary = models.CharField(_('Terpenes_Primary'), blank=True, null=True, max_length=255)
    terpenes_secondary = models.CharField(_('Terpenes_Secondary'), blank=True, null=True, max_length=255)
    parent_1 = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    parent_2 = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    cultivar_image = models.URLField(_('Image'), blank=True, null=True, max_length=255)
    lab_test_crm_id = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    modified_by = models.CharField(_('Modified By'), blank=True, null=True, max_length=255)
    created_by = models.CharField(_('Created By'), blank=True, null=True, max_length=255)
    create_time = models.DateTimeField(auto_now=False, blank=True, null=True)
    modify_time = models.DateTimeField(auto_now=False, blank=True, null=True)
    
    def __str__(self):
        return self.cultivar_name