from django.contrib import admin
from django.db import models
from .models import OrderVariable
# Register your models here.

class OrderVariableAdmin(admin.ModelAdmin):
    """
    ordering variables for fees
    """


admin.site.register(OrderVariable, OrderVariableAdmin)
