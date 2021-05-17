from django.contrib import admin
from django import forms
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.utils import timezone

from django_json_widget.widgets import JSONEditorWidget

from integration.inventory import (
    get_inventory_obj,
)
from  ..models import (
    Inventory,
    InventoryItemDelist,
)
from ..tasks import (
    notify_inventory_item_delist_approved_task,
)
from ..tasks.helpers import (
    get_approved_by
)
from .mixin import AdminApproveMixin
from ..data import(ITEM_CUSTOM_FIELD_ORG_MAP)


class InventoryItemDelistAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    list_display = (
        'name',
        'sku',
        'zoho_item_id',
        'vendor_name',
        'status',
        'approved_on',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        'name',
        # 'item_data',
        'status',
        'sku',
        'zoho_item_id',
        'cultivar_name',
        'vendor_name',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    write_only_fields = (
        'item',
    )
    fieldsets = (
        (None, {
            'fields': (
                'item',
                'name',
                'zoho_item_id',
                'sku',
                'cultivar_name',
                'vendor_name',
                # 'item_data',
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
    approve_button_label = 'Approve'
    # approve_button_color = '#ba2121'

    # formfield_overrides = {
    #     JSONField: {'widget': JSONEditorWidget(options={'modes':['code', 'text'], 'search': True, }, attrs={'disabled': 'disabled'})},
    #     # JSONField: {'widget': JSONEditorWidget},
    # }

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """
        if self.fieldsets:
            if obj:
                return tuple((x[0], {k: [f for f in v if f != 'item'] for k, v in x[1].items()}) for x in self.fieldsets)
            return self.fieldsets
        return [(None, {'fields': self.get_fields(request, obj)})]


    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != 'approved':
            return True
        return False

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            if obj.item:
                if obj.item.inventory_name and obj.item.inventory_name.lower() in ['efd', 'efl', 'efn']:
                    org = obj.item.inventory_name.lower()
                    inv_obj = get_inventory_obj(inventory_name=f'inventory_{org}')
                    data={'cf_cfi_published': False}
                    if org in ITEM_CUSTOM_FIELD_ORG_MAP:
                        org_cf_map = ITEM_CUSTOM_FIELD_ORG_MAP[org]
                        data={ org_cf_map[k]: v for k, v in data.items() if k in org_cf_map }
                    try:
                        result = inv_obj.update_item(obj.item.item_id, data, params={})
                    except Exception as exc:
                        self.message_user(request, f'Error while delisting item from Zoho Inventory:  {exc}', level='error')
                        print('Error while delisting item from Zoho Inventory')
                        print(exc)
                    else:
                        if result.get('code') == 0:
                            obj.status = 'approved'
                            obj.approved_on = timezone.now()
                            obj.approved_by = get_approved_by(request=request)
                            obj.save()
                            obj.item.cf_cfi_published = False
                            obj.item.save
                            self.message_user(request, 'This delisting is approved and item is delisted', level='success')
                            notify_inventory_item_delist_approved_task.delay(obj.id,)

                        else:
                            msg = result.get('message')
                            if msg:
                                self.message_user(request, f'Error while delisting item from Zoho Inventory:  {msg}', level='error')
                            else:
                                self.message_user(request, 'Error while delisting item from Zoho Inventory', level='error')
                            print('Error while deleting item from Zoho Inventory')
                            print(result)
                else:
                    self.message_user(request, 'Invalid Inventory Organization Name', level='error')
            else:
                self.message_user(request, 'No is item selected For action', level='error')
