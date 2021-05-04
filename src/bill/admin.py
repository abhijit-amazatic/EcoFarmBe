from django.contrib import admin
from bill.models import (Estimate, LineItem, )

class EstimateAdmin(admin.ModelAdmin):
    """
    Zoho Estimates
    """

class LineItemAdmin(admin.ModelAdmin):
    """
    LineItemAdmin configs.
    """
    def get_readonly_fields(self, request, obj=None):
        # make all fields readonly
        readonly_fields = list(
            set([field.name for field in self.opts.local_fields]))
        return readonly_fields
    
    list_display = ('sku', 'name', 'item_id', 'quantity', 'item_total','created_on',)
    search_fields = ('estimate__estimate_id','estimate__estimate_number','estimate__organization','estimate__customer_name','estimate__customer_id','sku','name',)
    ordering = ('-created_on',)

    
admin.site.register(Estimate, EstimateAdmin)
admin.site.register(LineItem, LineItemAdmin)


