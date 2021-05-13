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
    InventoryItemDelete,
)
from ..tasks import (
    notify_inventory_item_deletion_approved_task,
)
from ..tasks.helpers import (
    get_approved_by
)
from .mixin import AdminApproveMixin



class InventoryItemDeleteAdmin(AdminApproveMixin, admin.ModelAdmin):
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
    # form = InventoryItemDeleteForm
    approve_button_label = 'Approve Deletion'
    approve_button_color = '#ba2121'

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
                    inv_obj = get_inventory_obj(inventory_name=f'inventory_{obj.item.inventory_name.lower()}')
                    try:
                        result = inv_obj.delete_item(obj.item.item_id, params={})
                    except Exception as exc:
                        self.message_user(request, f'Error while deleting item from Zoho Inventory:  {exc}', level='error')
                        print('Error while creating item in Zoho Inventory')
                        print(exc)
                    else:
                        if result.get('code') in (0, 2006):
                            obj.status = 'approved'
                            obj.approved_on = timezone.now()
                            obj.approved_by = get_approved_by(request=request)
                            obj.save()
                            obj.item.delete()
                            self.message_user(request, 'This deletion is approved and item is deleted', level='success')
                            notify_inventory_item_deletion_approved_task.delay(obj.id,)

                        else:
                            msg = result.get('message')
                            if msg:
                                self.message_user(request, f'Error while deleting item from Zoho Inventory:  {msg}', level='error')
                            else:
                                self.message_user(request, 'Error while deleting item from Zoho Inventory', level='error')
                            print('Error while deleting item from Zoho Inventory')
                            print(result)
                else:
                    self.message_user(request, 'Invalid Inventory Organization Name', level='error')
            else:
                self.message_user(request, 'No is item selected For action', level='error')

