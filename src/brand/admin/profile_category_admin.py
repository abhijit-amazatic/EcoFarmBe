"""
Admin related customization.
"""
from django.contrib import admin

from ..models import (
    ProfileCategory,
)


class ProfileCategoryAdmin(admin.ModelAdmin):
    """
    ProfileCategoryAdmin
    """
    #search_fields = ('',)
