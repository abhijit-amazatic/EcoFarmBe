# from os import urandom
import random
from decimal import Decimal
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
# from django.contrib.postgres.fields import (ArrayField, JSONField,)
# from django.core.exceptions import ValidationError
# from django.db import models
# from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.text import Truncator
# from django.utils.encoding import force_str
from django.utils.html import mark_safe


from core import settings
from core.settings import (
    AWS_BUCKET,
)

from integration.apps.aws import (create_presigned_url, )
from integration.inventory import (
    get_inventory_obj,
    get_item_category_id,
    get_vendor_id_by_client_id,
)
from integration.tasks import (
    fetch_inventory_from_list_task,
)
from integration.crm import search_query
from integration.books import get_books_obj
from fee_variable.utils import (get_item_mcsp_fee,)
from core.mixins.admin import (CustomButtonMixin,)
from utils import (get_approved_by, )
from ..models import (
    CustomInventory,
    Documents,
)
from ..tasks import (
    create_approved_item_po_task,
    notify_inventory_item_approved_task,
)
from ..tasks.create_approved_item_po import (
    get_vendor_id,
)
from ..tasks.custom_inventory_data_from_crm import (
    get_custom_inventory_data_from_crm_vendor,
)
from ..utils import (
    get_item_tax,
)
from .custom_inventory_helpers import (get_new_item_data,)
from .custom_inventory_fieldsets import fieldsets


class InlineDocumentsAdmin(GenericStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    verbose_name = 'Document'
    verbose_name_plural = 'Documents'
    extra = 0
    readonly_fields = ('doc_type', 'file',)
    fields = ('doc_type', 'file',)
    model = Documents
    can_delete = False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(doc_type__in=('item_image', 'labtest'))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def file(self, obj):
        url = self.url(obj)
        if url and obj.doc_type == 'item_image':
            return mark_safe(
                '<div style="max-width: 500px;">'
                f'<a href="{url}" target="_blank">'
                f'<img src="{url}" style="width: 100%;height: auto;" alt="Image"/>'
                '</a></div>'
            )
        return mark_safe(f'<a href="{url}" target="_blank">{url}</a>')
    file.short_description = 'Uploaded File'
    file.allow_tags = True

    def url(self, obj):
        """
        Return s3 item image.
        """
        if obj.box_url:
            return obj.box_url
        try:
            url = create_presigned_url(AWS_BUCKET, obj.path)
            return url.get('response')
        except Exception:
            return None


class CustomInventoryForm(forms.ModelForm):
    # biomass_used_verified = forms.BooleanField(label='Used Trim Verified', initial=False, required=False)


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     instance = kwargs.get('instance')
    #     if instance and instance.zoho_organization:
    #         if instance.zoho_organization == 'efd':
    #             marketplace_status_choices = (
    #                 ('Vegging', _('Vegging')),
    #                 ('Flowering', _('Flowering')),
    #                 ('Processing', _('Processing')),
    #                 ('In-Testing', _('In-Testing')),
    #                 ('Available', _('Available')),
    #             )
    #             self.fields['marketplace_status'] = forms.ChoiceField(choices=marketplace_status_choices, required=True)
    #         elif instance.zoho_organization == 'efl':
    #             marketplace_status_choices =(
    #                 ('Vegging', _('Vegging')),
    #                 ('Flowering', _('Flowering')),
    #                 ('Processing', _('Processing')),
    #                 ('In-Testing', _('In-Testing')),
    #                 ('Available', _('Available')),
    #             )
    #             self.fields['marketplace_status'] = forms.ChoiceField(choices=marketplace_status_choices, required=True)
    #             self.fields['harvest_date'].label='Manufacturing Date'
    #         elif instance.zoho_organization  == 'efn':
    #             marketplace_status_choices =(
    #                 ('Rooting', _('Rooting')),
    #                 ('Available', _('Available')),
    #             )
    #             self.fields['marketplace_status'] = forms.ChoiceField(choices=marketplace_status_choices, required=True)
    #             self.fields['harvest_date'].label='Clone Date'

    # def clean_category_name(val):
    #     return super().clean_category_name()

    def clean(self):
        cleaned_data = super().clean()
        if hasattr(self, 'instance') and self.instance:
            if getattr(self, 'instance') and '_approve' in self.data:
                if self.instance.status == 'pending_for_approval':
                    if self.instance.category_name:
                        if self.instance.category_group in ('Isolates', 'Distillates', 'Concentrates', 'Terpenes'):
                            if cleaned_data.get('biomass_type') and cleaned_data.get('biomass_type') != 'Unknown':
                                if not cleaned_data.get('biomass_input_g'):
                                    self.add_error('biomass_input_g', "This value is required for current item category.")
                                if not cleaned_data.get('biomass_used_verified'):
                                    self.add_error('biomass_used_verified', "Please check Batch Record Document to verify used biomass quantity and mark as verified.")
                                    # raise ValidationError("Please check doc to verify used trim quantity and mark as verified.")
            return cleaned_data

    class Meta:
        model = CustomInventory
        fields = '__all__'


class CustomInventoryAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    Vendors Inventory Admin
    """
    form = CustomInventoryForm
    list_display = (
        'item_name',
        # 'sku',
        'category_name',
        'vendor_name',
        'license_profile',
        'grade_estimate',
        'quantity_available',
        'farm_ask_price',
        'marketplace_status',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        'item_name',
        'cultivar',
        'cultivar_name',
        'cultivar_type',
        'cultivar_crm_id',
        'category_name',
        'batch_record_file',
        'status',
        # 'vendor_name',
        'crm_vendor_id',
        # 'client_code',
        'procurement_rep',
        'zoho_item_id',
        'sku',
        'po_id',
        'po_number',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    inlines = [InlineDocumentsAdmin,]
    custom_buttons=('approve',)
    # custom_buttons_prop = {
    #     'approve': {
    #         'label': 'Approve',
    #         'color': '#ba2121',
    #     }
    # }

    def show_approve_button(self, request, obj,  add=False, change=False):
        return change and obj and obj.status == 'pending_for_approval'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('cultivar', 'license_profile', ).prefetch_related('extra_documents')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
            field.queryset = field.queryset.filter(status='approved')
        return field

    def has_change_permission(self, request, obj=None):
        if obj and obj.status == 'pending_for_approval':
            return True
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """
        if obj and obj.category_group in fieldsets:
            return fieldsets.get(obj.category_group, {})
        return fieldsets.get('default', {})

    def cultivar_name(self, obj):
        return obj.get_cultivar_name

    def generate_name(self, obj, request=None):
        if obj.category_group in ('Isolates', 'Distillates',):
            if not obj.cannabinoid_percentage:
                if request:
                    self.message_user(request, 'Error while generating item name, cannabinoid percentage not provided', level='error')
                return None
        return obj.item_name

    def generate_sku(self, obj, postfix, request=None):
        sku = []
        # if not settings.PRODUCTION and obj.zoho_organization in ['efl', 'efn']:
        #     sku.append('test')
        #     sku.append('sku')
        # sku.append(obj.client_code)

        if obj.category_group in ('Isolates', 'Distillates',):
            sku.append(str(obj.license_profile.license.client_id))
            if not obj.mfg_batch_id:
                if request:
                    self.message_user(request, 'Error while generating SKU, MFG Batch ID not provided', level='error')
                return None
            sku.append(obj.mfg_batch_id)

            if postfix:
                sku.append(str(postfix))

        elif obj.category_group in ('Flowers', 'Trims', 'Kief', 'Concentrates', 'Terpenes', 'Clones',):

            cultivar_name = self.cultivar_name(obj)

            if not cultivar_name:
                if request:
                    self.message_user(request, 'Error while generating SKU, cultivar name not provided', level='error')
                return None

            sku.append(cultivar_name.replace(' ', '-'))
            sku.append(str(obj.license_profile.license.client_id))

            # if obj.harvest_date:
            #     sku.append(obj.harvest_date.strftime('%m-%d-%y'))

            sku.append('{0:0>4}'.format(random.randint(1, 9999)))


        # if not settings.PRODUCTION:
        #     sku.append(force_str(urandom(3).hex()))

        return '-'.join(sku)

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            if not obj.license_profile:
                if request:
                    self.message_user(request, 'No license Profile assigned to the item.', level='error')
                return None
            item_name = self.generate_name(obj, request=request,)
            if item_name:
                if not obj.mcsp_fee:
                    obj.mcsp_fee = get_item_mcsp_fee(
                        obj.vendor_name,
                        license_profile=obj.license_profile,
                        item_category=obj.category_name,
                        request=request,
                        farm_price=obj.farm_ask_price
                    )
                if isinstance(obj.mcsp_fee, Decimal):
                    if not obj.cultivation_tax:
                        obj.cultivation_tax = get_item_tax(
                            category_name=obj.category_name,
                            biomass_type=obj.biomass_type,
                            biomass_input_g=obj.biomass_input_g,
                            total_batch_output=obj.total_batch_quantity,
                            request=request,
                        )
                    if isinstance(obj.cultivation_tax, Decimal):
                        if not obj.client_code or not obj.procurement_rep or not obj.crm_vendor_id:
                            get_custom_inventory_data_from_crm_vendor(obj, request)
                        if obj.zoho_organization:
                            inv_obj = get_inventory_obj(inventory_name=f'inventory_{obj.zoho_organization}')
                            metadata = {}
                            resp_metadata = inv_obj.get_metadata(params={})
                            if resp_metadata.get('code') == 0:
                                metadata = resp_metadata
                            category_id = get_item_category_id(
                                inv_obj=inv_obj,
                                category_name=obj.category_name,
                                metadata=metadata,
                            )
                            if category_id:
                                vendor_id = get_vendor_id(obj.license_profile, obj.zoho_organization)
                                if vendor_id:
                                    data = get_new_item_data(
                                        obj=obj,
                                        inv_obj=inv_obj,
                                        item_name=item_name,
                                        category_id=category_id,
                                        vendor_id=vendor_id,
                                    )
                                    self._approve(request, obj, inv_obj, data,)
                                else:
                                    self.message_user(request, 'Vendor not found on zoho', level='error')
                            else:
                                self.message_user(request, 'Invalid item category for selected Zoho inventory Organization', level='error')


    def _approve(self, request, obj, inv_obj, data, sku_postfix=0):
        sku = self.generate_sku(obj, postfix=sku_postfix, request=request,)
        if sku:
            data['sku'] = sku
            try:
                result = inv_obj.create_item(data, params={})
            except Exception as exc:
                self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                print('Error while creating item in Zoho Inventory')
                print(exc)
                print(data)
            else:
                if result.get('code') == 0:
                    item_id = result.get('item', {}).get('item_id')
                    if item_id:
                        obj.status = 'approved'
                        obj.zoho_item_id = item_id
                        obj.sku = sku
                        obj.approved_on = timezone.now()
                        obj.approved_by = get_approved_by(user=request.user)
                        obj.save()
                        self.message_user(request, 'This item is approved', level='success')
                        if obj.marketplace_status in ('In-Testing', 'Available'):
                            create_approved_item_po_task.delay(obj.id)
                            notify_inventory_item_approved_task.delay(obj.id)
                        else:
                            notify_inventory_item_approved_task.delay(obj.id, notify_logistics=False)
                        fetch_inventory_from_list_task.delay(f'inventory_{obj.zoho_organization}', [item_id])

                elif result.get('code') == 1001 and 'SKU' in result.get('message', '') and sku in result.get('message', 'item_id'):
                    self._approve(request, obj, inv_obj, data, sku_postfix=sku_postfix+1)
                else:
                    msg = result.get('message')
                    if msg:
                        self.message_user(request, f'Error while creating item in Zoho Inventory:  {msg}', level='error')
                    else:
                        self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                    print('Error while creating item in Zoho Inventory')
                    print(result)
                    print(data)

    # def test_action(self, request, queryset):
    #     pass


    def get_doc_url(self, obj, doc_types):
        """
        Return s3 license url.
        """
        try:
            # document_obj = Documents.objects.filter(object_id=obj.id, doc_type=doc_type).latest('created_on')
            document_obj = obj.extra_documents.filter(doc_type__in=doc_types).latest('created_on')
            if document_obj.box_url:
                return document_obj.box_url
            else:
                path = document_obj.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def batch_record_file(self, obj):
        url = self.get_doc_url(obj, doc_types=('trim_used_doc', 'item_batch_record'))
        if url:
            return mark_safe(f'<a href="{url}" target="_blank">{Truncator(url).chars(100)}</a>')
        else:
            return '-'
    # batch_record_file.short_description = 'Document'
    batch_record_file.short_description = 'Batch Record File'
    batch_record_file.allow_tags = True
