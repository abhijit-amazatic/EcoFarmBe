from os import urandom
from django import forms
from django.contrib.admin import widgets
from django.contrib import admin
from django.contrib.admin.utils import (unquote,)
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe

from simple_history.admin import SimpleHistoryAdmin
import nested_admin


from core import settings
from core.settings import (AWS_BUCKET, )

from integration.apps.aws import (create_presigned_url, )
from integration.inventory import (create_inventory_item, update_inventory_item, get_vendor_id, get_inventory_obj)
from integration.crm import search_query
from brand.models import (License, LicenseProfile,)
from fee_variable.utils import (get_tax_and_mcsp_fee,)
from ..tasks import (create_approved_item_po, notify_inventory_item_approved)
from .mixin import AdminApproveMixin
from ..models import (
    Inventory,
    CustomInventory,
    Documents,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
    InventoryItemsChangeRequest,
)
from .custom_inventory import CustomInventoryAdmin
from import_export import resources
from import_export.admin import (ImportExportModelAdmin,ExportActionMixin)




class InventoryItemsChangeRequestAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'item',
        'quantity_available',
        'farm_price',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        # 'status',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    fieldsets = (
        (None, {
            'fields': (
                'item',
                'farm_price',
                'quantity_available',
                'pricing_position',
                'have_minimum_order_quantity',
                'minimum_order_quantity',
                'payment_terms',
                'payment_method',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'approved_by',
                'approved_on',
                'created_by',
                'created_on',
                'updated_on',
            ),
        }),
    )
    # inlines = [InlineDocumentsAdmin,]
    # actions = ['test_action', ]


    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            tax_and_mcsp_fee = get_tax_and_mcsp_fee(obj.item.cf_vendor_name, request)
            if tax_and_mcsp_fee:
                data = obj.get_item_update_data()
                if obj.farm_price:
                    data['price'] = obj.farm_price + sum(tax_and_mcsp_fee)
                    data['rate'] = obj.farm_price + sum(tax_and_mcsp_fee)
                inventory_name = 'inventory_efd' if data.get('inventory_name') == 'EFD' else 'inventory_efl'
                data.pop('inventory_name')
                try:
                    result = update_inventory_item(inventory_name, data.get('item_id'), data)
                except Exception as exc:
                    self.message_user(request, 'Error while updating item in Zoho Inventory', level='error')
                    print('Error while updating item in Zoho Inventory')
                    print(exc)
                    print(data)
                else:
                    if result.get('code') == 0:
                        obj.status = 'approved'
                        obj.approved_on = timezone.now()
                        obj.approved_by = {
                            'email': request.user.email,
                            'phone': request.user.phone.as_e164,
                            'name': request.user.get_full_name(),
                        }
                        obj.save()
                        self.message_user(request, 'This change is approved and updated in', level='success')
                        # create_approved_item_po.apply_async((obj.id,), countdown=5)
                        # notify_inventory_item_approved.delay(obj.id)
                    else:
                        self.message_user(request, 'Error while updating item in Zoho Inventory', level='error')
                        print('Error while updating item in Zoho Inventory')
                        print(result)
                        print(data)

    def cultivar_name(self, obj):
            return obj.item.cultivar.cultivar_name
