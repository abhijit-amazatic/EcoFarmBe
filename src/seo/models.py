"""
SEO related schemas defined here.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.mixins.models import (StatusFlagMixin, TimeStampFlagModelMixin, )

class PageMeta(TimeStampFlagModelMixin, models.Model):
    """
    Stores webapp PageMeta.
    """
    page_url = models.CharField(_('Page URL'), max_length=512, unique=True, db_index=True)
    page_name = models.CharField(_('Page Name'), blank=True, null=True, max_length=255)
    page_title = models.CharField(_('Page Title'), blank=True, null=True, max_length=255)
    meta_title = models.CharField(_('Meta Title'), blank=True, null=True, max_length=255)
    meta_description = models.TextField(_('Meta Description'), blank=True, null=True )

    def __str__(self):
        return self.page_name

    class Meta:
        verbose_name = _('Page Meta')
