"""
Admin related customization.
"""
from django import forms
from django.contrib import admin
from django.conf import settings
from django.db import models
from .models import *



class OrderVariableAdmin(admin.ModelAdmin):
    """
    ordering variables for fees
    """

class CustomInventoryVariableAdmin(admin.ModelAdmin):
    """
    Custom Inventory Variables
    """
    
class TaxVariableAdmin(admin.ModelAdmin):
    """
    Tax Variables
    """
admin.site.register(OrderVariable, OrderVariableAdmin)
admin.site.register(CustomInventoryVariable, CustomInventoryVariableAdmin)
admin.site.register(TaxVariable, TaxVariableAdmin)
