from django.contrib import admin
from django.db import models

from django import forms
from .models import (
    PageMeta,
)


class PageMetaAdmin(admin.ModelAdmin):
    """
    Admin
    """
    list_display = (
        'page_url',
        'page_name',
        'page_title',
        'created_on',
        'updated_on',
    )
    search_fields = ('page_url', 'page_name', 'page_title',)
    # ordering = ('-page_name',)
    readonly_fields = (
        'created_on',
        'updated_on',
    )


admin.site.register(PageMeta, PageMetaAdmin)
