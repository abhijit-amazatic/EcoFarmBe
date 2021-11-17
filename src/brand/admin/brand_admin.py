"""
Admin related customization.
"""

from django.contrib import admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from ..models import (
    Brand, )


class BrandAdmin(admin.ModelAdmin):
    """
    Configuring brand
    """
    extra = 0
    model = Brand
    list_display = (
        'brand_name',
        'organization',
        'appellation',
        'created_on',
        'updated_on',
    )
    search_fields = ('brand_name', 'organization', 'appellation')
    list_filter = (
        ('created_on', DateRangeFilter),
        ('updated_on', DateRangeFilter),
    )
    ordering = (
        '-created_on',
        'updated_on',
    )
