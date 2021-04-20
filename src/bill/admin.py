from django.contrib import admin
from bill.models import (Estimate, )

class EstimateAdmin(admin.ModelAdmin):
    """
    Zoho Estimates
    """
admin.site.register(Estimate, EstimateAdmin)