"""
Admin related customization.
"""
from django import forms
from django.contrib import admin

from django.conf import settings
from django.db import models
from datetime import datetime
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils import timezone


class OrderVariableAdmin(admin.ModelAdmin):
    """
    ordering variables for fees
    """

admin.site.register(OrderVariable, OrderVariableAdmin)
