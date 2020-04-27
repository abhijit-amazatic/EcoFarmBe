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
    STATUS_CHOICES = ((STATUS_NOT_STARTED, _('Not Started')),
                      (STATUS_IN_PROGRESS, _('In Progress')),
                      (STATUS_APPROVED, _('Approved')),
                      (STATUS_DONE, _('Done')),
                      (STATUS_COMPLETED, _('Completed')))
    status = models.CharField(choices=STATUS_CHOICES,
                              max_length=20, default=None, null=True, blank=True)
    step  = models.CharField(_('Steps'), blank=True, null=True, max_length=255)

    class Meta:
        abstract = True

