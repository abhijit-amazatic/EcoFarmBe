from os import urandom
from django import forms
from django.contrib.admin import widgets
from django.contrib import admin
from django.contrib.admin.utils import (unquote,)
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.db import models
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe
from core import settings

from integration.apps.aws import (create_presigned_url, )

from core.settings import (AWS_BUCKET, )

import nested_admin
from integration.inventory import (create_inventory_item, update_inventory_item, get_vendor_id, get_inventory_obj)
from integration.crm import search_query
from brand.models import (License, LicenseProfile,)
from fee_variable.models import (CustomInventoryVariable, TaxVariable)
from .tasks import (create_approved_item_po, notify_inventory_item_approved)
from .models import (
    Inventory,
    CustomInventory,
    Documents,
    DailyInventoryAggrigatedSummary,
    County,
    CountyDailySummary,
)
from import_export import resources
from import_export.admin import (ImportExportModelAdmin,ExportActionMixin)


def get_category_id(category_name):
    name_id_map = {
        'ROOT': '-1',
        'Wholesale - Flower':                       '2155380000000446107',
        'In the Field':                             '2155380000000446105',
        'Flower - Tops':                            '2155380000001179966',
        'Flower - Bucked Untrimmed':                '2155380000001179970',
        'Flower - Bucked Untrimmed - Seeded':       '2155380000001179986',
        'Flower - Bucked Untrimmed - Contaminated': '2155380000001179990',
        'Flower - Small':                           '2155380000009002152',
        'Trim':                                     '2155380000001138013',
        'Packaged Goods':                           '2155380000001138015',
        'Isolates':                                 '2155380000001138017',
        'Isolates - CBD':                           '2155380000001179992',
        'Isolates - THC':                           '2155380000001187003',
        'Isolates - CBG':                           '2155380000001339007',
        'Isolates - CBN':                           '2155380000001339009',
        'Wholesale - Concentrates':                 '2155380000001138019',
        'Crude Oil':                                '2155380000001178426',
        'Crude Oil - THC':                          '2155380000001178430',
        'Crude Oil - CBD':                          '2155380000001178432',
        'Distillate Oil':                           '2155380000001178428',
        'Distillate Oil - THC':                     '2155380000001178434',
        'Distillate Oil - CBD':                     '2155380000001178436',
        'Shatter':                                  '2155380000001339001',
        'Sauce':                                    '2155380000001339003',
        'Crumble':                                  '2155380000001339005',
        'Kief':                                     '2155380000001501335',
        'Hash':                                     '2155380000009512784',
        'Lab Testing':                              '2155380000001213350',
        'Terpenes':                                 '2155380000001295002',
        'Terpenes - Cultivar Specific':             '2155380000001295004',
        'Terpenes - Cultivar Blended':              '2155380000001295006',
        'Services':                                 '2155380000001889003',
        'QC':                                       '2155380000001889005',
        'Transport':                                '2155380000004337546',
        'Secure Cash Handling':                     '2155380000004337548',
    }
    return name_id_map.get(category_name, '')

custom_inventory_variable_program_map = {
    'spot market farm': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_BRONZE,
    },
    'integrated farm partner silver': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_SILVER,
    },
    'integrated farm partner gold': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IFP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_GOLD,
    },
    'Silver - Member': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IBP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_SILVER,
    },
    'Gold - VIP': {
        'program_type': CustomInventoryVariable.PROGRAM_TYPE_IBP,
        'tier': CustomInventoryVariable.PROGRAM_TIER_GOLD,
    },
}



class InlineDocumentsAdmin(GenericStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    extra = 0
    readonly_fields = ('doc_type', 'file',)
    fields = ('doc_type', 'file',)
    model = Documents
    can_delete = False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # inventory = get_inventory_obj(inventory_name='inventory_efd')
        # result = inventory.get_user()
        # if result.get('code') == 0:
        #     procurement_rep = [(o.get('email'), o.get('name')) for o in result.get('users', []) if o.get('status') in ['active', 'invited']]
        #     procurement_rep.insert(0, ('', '-------'))
        #     self.fields['procurement_rep'] = forms.ChoiceField(choices=procurement_rep, required=False)

    class Meta:
        model = CustomInventory
        fields = '__all__'



# Register your models here.
class CustomInventoryAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    change_form_template = 'inventory/custom_inventory_change_form.html'
    list_display = ('cultivar_name', 'category_name', 'grade_estimate', 'quantity_available', 'farm_ask_price', 'status', 'created_on', 'updated_on',)
    # readonly_fields = ( 'status', 'cultivar_name', 'created_on', 'updated_on', 'vendor_name', 'zoho_item_id', 'sku', 'created_by', 'approved_by', 'approved_on',)
    readonly_fields = (
        'cultivar_name',
        'status',
        # 'vendor_name',
        'crm_vendor_id',
        # 'client_code',
        'procurement_rep',
        'zoho_item_id',
        'sku',
        'books_po_id',
        'po_number',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    inlines = [InlineDocumentsAdmin,]
    # actions = ['test_action', ]
    form = CustomInventoryForm
    fieldsets = (
        ('BATCH & QUALITY INFORMATION', {
            'fields': (
                'cultivar',
                'cultivar_name',
                'category_name',
                'quantity_available',
                'harvest_date',
                'need_lab_testing_service',
                'batch_availability_date',
                'grade_estimate',
                'product_quality_notes',
        ),
        }),
        ('PRICING INFORMATION', {
            'fields': (
                'farm_ask_price',
                'pricing_position',
                # 'have_minimum_order_quantity',
                # 'minimum_order_quantity',
            ),
        }),
        ('SAMPLE LOGISTICS (PICKUP OR DROP OFF)', {
            'fields': (
                'transportation',
                'best_contact_Day_of_week',
                'best_contact_time_from',
                'best_contact_time_to',
            ),
        }),
        ('PAYMENT', {
            'fields': (
                'payment_terms',
                'payment_method',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'vendor_name',
                'crm_vendor_id',
                'client_code',
                'procurement_rep',
                'zoho_item_id',
                'sku',
                'books_po_id',
                'po_number',
                'approved_by',
                'approved_on',
                'created_by',
                'created_on',
                'updated_on',
            ),
        }),
    )

    def response_change(self, request, obj):
        if '_approve' in request.POST:
            if obj.status == 'pending_for_approval':
                self.approve(request, obj)
            return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
                field.queryset = field.queryset.filter(status='approved')
        return field

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.status == 'pending_for_approval' and change:
            context['show_approve'] = True
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def generate_sku(self, obj):
        sku = []
        if not settings.PRODUCTION:
            sku.append('test')
        sku.append('sku')
        sku.append(obj.client_code)
        sku.append(obj.cultivar.cultivar_name)

        if obj.harvest_date:
            sku.append(obj.harvest_date.strftime('%m-%d-%y'))

        if not settings.PRODUCTION:
            sku.append(force_str(urandom(3).hex()))

        return '-'.join(sku)

    def get_crm_data(self, request, obj):
        found_code = False
        if obj.vendor_name:
            try:
                result = search_query('Vendors', obj.vendor_name, 'Vendor_Name')
            except Exception :
                self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')
            else:
                if result.get('status_code') == 200:
                    data_ls = result.get('response')
                    if data_ls and isinstance(data_ls, list):
                        for vendor in data_ls:
                            if vendor.get('Vendor_Name') == obj.vendor_name:
                                if not obj.crm_vendor_id:
                                    obj.crm_vendor_id = vendor.get('id', '')
                                if not obj.procurement_rep:
                                    p_rep = vendor.get('Owner', {}).get('email')
                                    if p_rep:
                                        obj.procurement_rep = p_rep
                                    p_rep_name = vendor.get('Owner', {}).get('name')
                                    if p_rep_name:
                                        obj.procurement_rep_name = p_rep_name
                                client_code = vendor.get('Client_Code')
                                if client_code:
                                    found_code = True
                                    obj.client_code = client_code
                                    return client_code

                if result.get('status_code') == 204 or not found_code:
                    try:
                        result = search_query('Accounts', obj.vendor_name, 'Account_Name')
                    except Exception :
                        self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')
                    else:
                        if result.get('status_code') == 200:
                            data_ls = result.get('response')
                            if data_ls and isinstance(data_ls, list):
                                for vendor in data_ls:
                                    if vendor.get('Account_Name') == obj.vendor_name:
                                        if not obj.procurement_rep:
                                            p_rep = vendor.get('Owner', {}).get('email')
                                            if p_rep:
                                                obj.procurement_rep = p_rep
                                            p_rep_name = vendor.get('Owner', {}).get('name')
                                            if p_rep_name:
                                                obj.procurement_rep_name = p_rep_name
                                        client_code = vendor.get('Client_Code')
                                        if client_code:
                                            obj.client_code = client_code
                                            return client_code
                                        else:
                                            self.message_user(request, f'client code not found for vendor \'{obj.vendor_name}\' in Zoho CRM', level='error')
                                self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                        elif result.get('status_code') == 204 or not found_code:
                            self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                else:
                    self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')

        return None

    def tax_and_mcsp_fee(self, request, obj):
        lp = LicenseProfile.objects.filter(name=obj.vendor_name).first()
        if lp:
            try:
                program_overview = lp.license.program_overview
            except License.program_overview.RelatedObjectDoesNotExist:
                self.message_user(request, 'program overview not exist', level='error')
            else:
                ifp_tier_name = program_overview.program_details.get('program_name', '')
                tier = custom_inventory_variable_program_map.get(ifp_tier_name, {})
                if tier:
                    InventoryVariable = CustomInventoryVariable.objects.filter(**tier).first()
                    if InventoryVariable and InventoryVariable.mcsp_fee:
                        tax_var = TaxVariable.objects.latest('updated_on')
                        if tax_var and tax_var.cultivar_tax:
                            return float(InventoryVariable.mcsp_fee)+float(tax_var.cultivar_tax)
                        else:
                            self.message_user(request, 'No Cultivar Tax found.', level='error')
                    else:
                        self.message_user(request, 'No MCSP fee found for profile.', level='error')
                else:
                    self.message_user(request, 'No program tier found for profile.', level='error')

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            tax_and_mcsp_fee = self.tax_and_mcsp_fee(request, obj)
            if tax_and_mcsp_fee:
                if not obj.client_code or not obj.procurement_rep or not obj.crm_vendor_id:
                    self.get_crm_data(request, obj)
                if obj.client_code:
                    sku = self.generate_sku(obj)

                    data = {}
                    data['item_type'] = 'inventory'
                    data['cf_client_code'] = obj.client_code
                    data['sku'] = sku
                    data['unit'] = 'lb'

                    data['name'] = obj.cultivar.cultivar_name
                    data['cf_cultivar_name'] = obj.cultivar.cultivar_name
                    data['cf_strain_name'] = obj.cultivar.cultivar_name

                    if obj.cultivar.cultivar_type:
                        data['cf_cultivar_type'] = obj.cultivar.cultivar_type

                    if obj.category_name and settings.PRODUCTION:
                        data['category_name'] = obj.category_name
                        data['category_id'] = get_category_id(obj.category_name)

                    if obj.harvest_date:
                        data['cf_harvest_date'] = str(obj.harvest_date)  # not in inventor

                    if obj.batch_availability_date:
                        data['cf_date_available'] = str(obj.batch_availability_date)

                    if obj.grade_estimate:
                        data['cf_grade_seller'] = obj.grade_estimate

                    if obj.product_quality_notes:
                        data['cf_batch_quality_notes'] = obj.product_quality_notes

                    if obj.need_lab_testing_service is not None:
                        data['cf_lab_testing_services'] = 'Yes' if obj.need_lab_testing_service else 'No'

                    if obj.farm_ask_price:
                        data['cf_farm_price'] = str(int(obj.farm_ask_price))
                        data['cf_farm_price_2'] = obj.farm_ask_price
                        # data['purchase_rate'] = obj.farm_ask_price
                        data['rate'] = obj.farm_ask_price + tax_and_mcsp_fee

                    if obj.pricing_position:
                        data['cf_seller_position'] = obj.pricing_position
                    if obj.have_minimum_order_quantity:
                        data['cf_minimum_quantity'] = int(obj.minimum_order_quantity)

                    if obj.vendor_name:
                        data['cf_vendor_name'] = obj.vendor_name
                        # data['vendor_name'] = obj.vendor_name

                    if obj.payment_terms:
                        data['cf_payment_terms'] = obj.payment_terms

                    if obj.payment_method:
                        data['cf_payment_method'] = obj.payment_method

                    if obj.procurement_rep:
                        data['cf_procurement_rep'] = obj.procurement_rep

                    # data['initial_stock'] = int(obj.quantity_available)
                    data['product_type'] = 'goods'
                    data['cf_sample_in_house'] = 'Pending'
                    data['cf_status'] = 'In-Testing'
                    data['cf_cfi_published'] = False
                    data['account_id'] = 2155380000000448337 if settings.PRODUCTION else 2185756000001423419
                    # data['account_name'] = '3rd Party Flower Sales'
                    data['purchase_account_id'] = 2155380000000565567 if settings.PRODUCTION else 2185756000001031365
                    # data['purchase_account_name'] = 'Product Costs - Flower'
                    data['inventory_account_id'] = 2155380000000448361 if settings.PRODUCTION else 2185756000001423111
                    # data['inventory_account_name'] = 'Inventory - In the Field'

                    # data['warehouses'] = [
                    #     {
                    #         "warehouse_id": "2155380000000782007",
                    #         # "warehouse_name": "In the Field Inventory ",
                    #         # "is_primary": True,
                    #         # "warehouse_stock_on_hand": 0.0,
                    #         "initial_stock": 1,
                    #         "initial_stock_rate": 1,
                    #         # "warehouse_available_stock": 0.0,
                    #         # "warehouse_actual_available_stock": 0.0,
                    #         # "warehouse_committed_stock": 0.0,
                    #         # "warehouse_actual_committed_stock": 0.0,
                    #         # "warehouse_available_for_sale_stock": 0.0,
                    #         # "warehouse_actual_available_for_sale_stock": 0.0,
                    #     },
                    # ]

                    data['is_taxable'] = True

                    try:
                        result = create_inventory_item(inventory_name='inventory_efd', record=data, params={})
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
                                    obj.approved_by = {
                                        'email': request.user.email,
                                        'phone': request.user.phone.as_e164,
                                        'name': request.user.get_full_name(),
                                    }
                                    obj.save()
                                    self.message_user(request, 'This item is approved')
                                    create_approved_item_po.apply_async((obj.id,), countdown=5)
                                    notify_inventory_item_approved.delay(obj.id)
                        else:
                            self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                            print('Error while creating item in Zoho Inventory')
                            print(result)
                            print(data)

    def cultivar_name(self, obj):
            return obj.cultivar.cultivar_name

    # def test_action(self, request, queryset):
    #     pass


class DailyInventoryAggrigatedSummaryResource(resources.ModelResource):

    class Meta:
        model = DailyInventoryAggrigatedSummary
        fields = ('date','total_thc_max','total_thc_min','batch_varities','average','total_value','smalls_quantity','tops_quantity','total_quantity','trim_quantity',)
        #exclude = ('imported', )
        #export_order = ('id', 'price', 'author', 'name')
        
class DailyInventoryAggrigatedSummaryAdmin(ExportActionMixin,admin.ModelAdmin):
    """
    Summary Admin.
    """
    model = DailyInventoryAggrigatedSummary
    search_fields = ('date',)
    list_display = ('date',)
    ordering = ('-date',)
    readonly_fields = ('date','total_thc_max','total_thc_min','batch_varities','average','total_value','smalls_quantity','tops_quantity','total_quantity','trim_quantity',)
    resource_class = DailyInventoryAggrigatedSummaryResource


class InlineCountyDailySummaryAdminResource(resources.ModelResource):

    class Meta:
        model = CountyDailySummary
        fields = ('date','county__name','total_thc_max','total_thc_min','batch_varities','average','total_value','smalls_quantity','tops_quantity','total_quantity','trim_quantity',)
        
        
class InlineCountyDailySummaryAdmin(admin.TabularInline):
    extra = 0
    model = CountyDailySummary
    list_display = ('date', 'county__name',)
    readonly_fields = ('date','county','total_thc_max','total_thc_min','batch_varities','average','total_value','smalls_quantity','tops_quantity','total_quantity','trim_quantity',)
    search_fields = ('date', 'county__name',)
    can_delete = False
    
    


class CountyAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    """
    Admin
    """
    inlines = (InlineCountyDailySummaryAdmin,)
    model = County
    search_fields = ('name',)
    ordering = ('-name',)
    readonly_fields = ('name',)
    resource_class = InlineCountyDailySummaryAdminResource
    

admin.site.register(County, CountyAdmin)
admin.site.register(DailyInventoryAggrigatedSummary, DailyInventoryAggrigatedSummaryAdmin)
admin.site.register(CustomInventory, CustomInventoryAdmin)


