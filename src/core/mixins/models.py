"""
Basic building mixins.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _


class StatusFlagMixin(models.Model):
    """
    This mixin addds Status & steps field to a model
    """
    STATUS_NOT_STARTED = 'not_started'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_APPROVED = 'approved'
    STATUS_DONE = 'done'
    STATUS_CROP = 'crop_overview'
    STATUS_FINANCIAL = 'financial_overview'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = ((STATUS_NOT_STARTED, _('Not Started')),
                      (STATUS_IN_PROGRESS, _('In Progress')),
                      (STATUS_COMPLETED, _('Completed')),
                      (STATUS_APPROVED, _('Approved')),
                      (STATUS_CROP, _('Crop Overview')),
                      (STATUS_FINANCIAL, _('Financial Overview')),
                      (STATUS_EXPIRED, _('Expired')),
                      (STATUS_DONE, _('Done')))
    status = models.CharField(choices=STATUS_CHOICES,
                              max_length=20, default=STATUS_NOT_STARTED, null=False, blank=False)
    step  = models.CharField(_('Steps'),default='0',blank=False, null=False, max_length=255)

    class Meta:
        abstract = True


class TimeStampFlagModelMixin(models.Model):
    """
    Mixin to add timestamp fields to a Model
    """
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True       
