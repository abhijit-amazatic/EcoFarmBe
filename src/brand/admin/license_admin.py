"""
Admin related customization.
"""
import json
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.postgres import fields
from django.db import transaction
from django.utils import timezone

from nested_admin import NestedStackedInline, NestedModelAdmin
from django_json_widget.widgets import JSONEditorWidget
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

from core.mailer import mail_send
from integration.box import (
    delete_file,
)
from utils import (
    reverse_admin_change_path,
)
from ..tasks import (
    insert_record_to_crm,
    invite_profile_contacts_task,
    create_customer_in_books_task,
    refresh_integration_ids_task,
)
from core.utility import (
    send_async_approval_mail,
    get_profile_type,
    send_async_approval_mail_admin,
)
from ..models import (
    License,
    ProfileContact,
    LicenseProfile,
    CultivationOverview,
    NurseryOverview,
    ProgramOverview,
    FinancialOverview,
    CropOverview,
)
from .license_admin_export_resource import LicenseResource


def get_obj_file_ids(obj):
    """
    Extract box file ids
    """
    box_file_ids = []
    # doc_field = ['uploaded_license_to','uploaded_sellers_permit_to']
    links = License.objects.filter(id=obj.id).values(
        "uploaded_license_to", "uploaded_sellers_permit_to"
    )
    to_be_removed = [v for k, v in links[0].items() if v is not None]
    try:
        if links:
            for doc in to_be_removed:
                if "?id=" in doc:
                    box_id = doc.split("?id=")[1]
                else:
                    box_id = doc
                if box_id:
                    box_file_ids.append(box_id)
            return box_file_ids
    except Exception as e:
        print("exception", e)


json_field_overide = {
    fields.JSONField: {
        "widget": JSONEditorWidget(options={"modes": ["code", "text"], "search": True})
    },
}


class InlineLicenseProfileContactAdmin(NestedStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """

    extra = 0
    model = ProfileContact
    readonly_fields = ("is_draft",)
    can_delete = False
    formfield_overrides = json_field_overide


class InlineCultivationOverviewAdmin(NestedStackedInline):
    """
    Configuring field admin view for CultivationOverview.
    """

    extra = 0
    model = CultivationOverview
    readonly_fields = (
        "is_draft",
        "overview",
    )
    can_delete = False
    formfield_overrides = json_field_overide


class InlineNurseryOverviewAdmin(NestedStackedInline):
    """
    Configuring field admin view for NurseryOverview.
    """

    extra = 0
    model = NurseryOverview
    can_delete = False
    # readonly_fields = ('is_draft','overview',)


class InlineFinancialOverviewAdmin(NestedStackedInline):
    """
    Configuring field admin view for FinancialOverview model.
    """

    extra = 0
    model = FinancialOverview
    can_delete = False
    readonly_fields = (
        "is_draft",
        "overview",
    )
    formfield_overrides = json_field_overide


class InlineCropOverviewAdmin(NestedStackedInline):
    """
    Configuring field admin view for InlineCropOverview model.
    """

    extra = 0
    model = CropOverview
    can_delete = False
    readonly_fields = (
        "is_draft",
        "overview",
    )
    formfield_overrides = json_field_overide


class InlineProgramOverviewAdmin(NestedStackedInline):
    """
    Configuring field admin view for InlineProgramOverviewAdmin  model
    """

    extra = 0
    model = ProgramOverview
    can_delete = False
    readonly_fields = ("is_draft",)


class InlineLicenseProfileAdmin(NestedStackedInline):
    """
    Configuring field admin view for InlineLicenseProfile  model
    """

    extra = 0
    model = LicenseProfile
    can_delete = False
    readonly_fields = (
        "name",
        "is_draft",
        "agreement_signed",
    )
    exclude = (
        "name",
        "is_account_updated_in_crm",
        "is_vendor_updated_in_crm",
    )

    def get_fields(self, request, obj):
        fields = list(super().get_fields(request, obj))
        fields.remove("name")
        return ["name"] + fields


# class InlineLicenseUserAdmin(NestedTabularInline):
#     extra = 0
#     model = LicenseUser


class LicenseUpdatedForm(forms.ModelForm):
    class Meta:
        model = License
        fields = "__all__"

    def clean(self):
        if self.changed_data and "status" in self.changed_data:
            if self.cleaned_data.get("status") == "approved":
                license_obj = License.objects.filter(id=self.instance.id)
                if license_obj:
                    ac_manager = license_obj[0].created_by.email
                    profile_type = get_profile_type(license_obj[0])
                    admin_link = f"https://{settings.BACKEND_DOMAIN_NAME}{reverse_admin_change_path(license_obj[0])}"
                    mail_send(
                        "farm-approved.html",
                        {
                            "link": settings.FRONTEND_DOMAIN_NAME + "login",
                            "profile_type": profile_type,
                            "legal_business_name": license_obj[0].legal_business_name,
                        },
                        "Your %s profile has been approved." % profile_type,
                        ac_manager,
                    )
                    # admin mail send after approval
                    mail_send(
                        "farm-approved-admin.html",
                        {
                            "admin_link": admin_link,
                            "mail": self.request.user.email,
                            "license_type": license_obj[0].license_type,
                            "legal_business_name": license_obj[0].legal_business_name,
                            "license_number": license_obj[0].license_number,
                        },
                        "License Profile [%s] approved" % license_obj[0].license_number,
                        recipient_list=settings.ONBOARDING_ADMIN_EMAIL,
                    )


class LicenseAdmin(ImportExportModelAdmin, NestedModelAdmin):
    """
    #ExportActionMixin
    #ImportExportModelAdmin
    Configuring License
    """

    integration_fields = (
        "zoho_crm_id",
        "crm_license",
        "zoho_crm_account_id",
        "crm_account",
        "zoho_crm_vendor_id",
        "crm_vendor",
        "zoho_books_customer_ids",
        "zoho_books_vendor_ids",
        "crm_output_display",
        "books_output_display",
    )

    def get_form(self, request, *args, **kwargs):
        form = super(LicenseAdmin, self).get_form(request, *args, **kwargs)
        form.request = request
        return form

    def get_list_display(self, request):
        if request.user.email in getattr(settings, "INTEGRATION_ADMIN_EMAILS", []):
            return self.list_display_integration_admin
        return self.list_display

    def get_fieldsets(self, request, obj=None):
        """
        Hook for specifying fieldsets.
        """

        if self.fieldsets:
            return self.fieldsets
        return [
            (None, {
                "fields": (
                    f
                    for f in self.get_fields(request, obj)
                    if f not in self.integration_fields
                ),
            }),
            ("Integration Info", {
                "classes": ("collapse",),
                "fields": self.integration_fields,
            }),
        ]

    def crm_output_display(self, obj):
        jw = JSONEditorWidget(
            options={"modes": ["code", "text", "view"], "search": True}
        )
        return jw.render(
            "CRM Output",
            json.dumps(obj.crm_output or {}),
            attrs={"id": "crm_output_display"},
        )

    crm_output_display.short_description = "CRM Output"

    def books_output_display(self, obj):
        jw = JSONEditorWidget(
            options={"modes": ["code", "text", "view"], "search": True}
        )
        return jw.render(
            "Books Output",
            json.dumps(obj.books_output or {}),
            attrs={"id": "books_output_display"},
        )

    books_output_display.short_description = "Books output"

    def approved_on(self, obj):
        return obj.license_profile.approved_on

    def name(self, obj):
        return obj.license_profile.name

    def approved_by(self, obj):
        if obj.license_profile.approved_by:
            return obj.license_profile.approved_by.get("email", "N/A")
        return "N/A"

    def business_dba(self, obj):
        if obj.license_profile:
            return obj.license_profile.business_dba

    business_dba.admin_order_field = "-license_profile__business_dba"

    def zoho_crm_account_id(self, obj):
        if obj.license_profile:
            return obj.license_profile.zoho_crm_account_id

    zoho_crm_account_id.admin_order_field = "-license_profile__zoho_crm_account_id"

    def zoho_crm_vendor_id(self, obj):
        if obj.license_profile:
            return obj.license_profile.zoho_crm_vendor_id

    zoho_crm_vendor_id.admin_order_field = "-license_profile__zoho_crm_vendor_id"

    def crm_license(self, obj):
        return obj.is_updated_in_crm

    crm_license.boolean = True
    crm_license.admin_order_field = "-is_updated_in_crm"
    crm_license.short_description = "license"

    def crm_account(self, obj):
        if obj.license_profile:
            return obj.license_profile.is_account_updated_in_crm

    crm_account.boolean = True
    crm_account.admin_order_field = "-license_profile__is_account_updated_in_crm"
    crm_account.short_description = "account"

    def crm_vendor(self, obj):
        if obj.license_profile:
            return obj.license_profile.is_vendor_updated_in_crm

    crm_vendor.boolean = True
    crm_vendor.admin_order_field = "-license_profile__is_vendor_updated_in_crm"
    crm_vendor.short_description = "vendor"

    def get_search_results(self, request, queryset, search_term):
        """
        Default and custom search filter for farm names.
        """
        queryset, use_distinct = super(LicenseAdmin, self).get_search_results(
            request, queryset, search_term
        )
        queryset |= self.model.objects.select_related("license_profile").filter(
            license_profile__name__contains={"name": search_term}
        )
        return queryset, use_distinct

    name.admin_order_field = "license_profile__name"
    inlines = [
        InlineLicenseProfileAdmin,
        InlineLicenseProfileContactAdmin,
        InlineCultivationOverviewAdmin,
        InlineNurseryOverviewAdmin,
        InlineFinancialOverviewAdmin,
        InlineCropOverviewAdmin,
        InlineProgramOverviewAdmin,
    ]
    resource_class = LicenseResource
    form = LicenseUpdatedForm
    extra = 0
    model = License
    list_display = (
        "business_dba",
        "client_id",
        "license_number",
        "legal_business_name",
        "organization",
        "brand",
        "profile_category",
        "status",
        "approved_on",
        "approved_by",
        "created_on",
        "updated_on",
    )
    list_display_integration_admin = (
        "business_dba",
        "client_id",
        "license_number",
        "legal_business_name",
        "profile_category",
        "status",
        "zoho_crm_id",
        "zoho_crm_account_id",
        "zoho_crm_vendor_id",
        "crm_license",
        "crm_account",
        "crm_vendor",
        "zoho_books_customer_ids",
        "zoho_books_vendor_ids",
        "approved_on",
        "approved_by",
        "created_on",
        "updated_on",
    )

    list_select_related = [
        "brand__organization__created_by",
        "organization__created_by",
    ]
    search_fields = (
        "license_number",
        "legal_business_name",
        "client_id",
        "license_profile__business_dba",
        "brand__brand_name",
        "brand__organization__created_by__email",
        "organization__name",
        "organization__created_by__email",
    )
    readonly_fields = (
        "created_on",
        "updated_on",
        "client_id",
        "crm_output_display",
        "books_output_display",
        "is_updated_in_crm",
        "crm_license",
        "zoho_crm_account_id",
        "crm_account",
        "zoho_crm_vendor_id",
        "crm_vendor",
    )
    list_filter = (
        ("created_on", DateRangeFilter),
        ("updated_on", DateRangeFilter),
        "status",
        "license_status",
        "profile_category",
        "is_contract_downloaded",
        "license_type",
    )
    ordering = (
        "-created_on",
        "legal_business_name",
        "status",
        "updated_on",
    )
    exclude = (
        "is_seller",
        "is_buyer",
        "crm_output",
        "books_output",
    )
    actions = [
        "temporary_approve_license_profile",
        "approve_license_profile",
        "update_status_to_in_progress",
        "delete_model",
        "sync_records",
        "update_records",
        "update_books_records",
        "refresh_integration_ids",
    ]
    list_per_page = 50

    verbose_name = "My Book"
    verbose_name_plural = "My Books"

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if "status" in form.changed_data and obj.status == "approved":
            send_async_approval_mail.delay(obj.id)
            send_async_approval_mail_admin.delay(obj.id, request.user.id)
            license_profile = LicenseProfile.objects.filter(license=obj)
            if license_profile:
                license_profile[0].approved_on = timezone.now()
                license_profile[0].approved_by = request.user.get_user_info()
                license_profile[0].save()
            if hasattr(obj, "profile_contact"):
                invite_profile_contacts_task.delay(obj.profile_contact.id)
                # add_users_to_system_and_license.delay(obj.profile_contact.id,obj.id)
        super().save_model(request, obj, form, change)

    ################### Actions ####################
    def temporary_approve_license_profile(self, request, queryset):
        """
        Function for bulk profile approval.
        """
        for profile in queryset:
            if profile.status != "approved":
                profile.status = "approved"
                profile.save()
        messages.success(request, "License Profiles Temporarily Approved!")

    temporary_approve_license_profile.short_description = (
        "Temporary Selected License Profiles"
    )

    def approve_license_profile(self, request, queryset):
        """
        Function for bulk profile approval.
        """
        for profile in queryset:
            if profile.status != "approved":
                profile.status = "approved"
                profile.save()
                license_profile = LicenseProfile.objects.filter(license=profile)
                if license_profile:
                    license_profile[0].approved_on = timezone.now()
                    license_profile[0].approved_by = request.user.get_user_info()
                    license_profile[0].save()
                send_async_approval_mail.delay(profile.id)
                send_async_approval_mail_admin.delay(profile.id, request.user.id)
                if hasattr(profile, "profile_contact"):
                    invite_profile_contacts_task.delay(profile.profile_contact.id)
                    # add_users_to_system_and_license.delay(profile.profile_contact.id,profile.id)
        messages.success(request, "License Profiles Approved!")

    approve_license_profile.short_description = "Approve Selected License Profiles"

    def delete_model(self, request, queryset):
        for obj in queryset:
            file_ids = get_obj_file_ids(obj)
            if file_ids:
                for file_id in file_ids:
                    print("FileID to delete from box:", file_id)
                    delete_file(file_id)
            obj.delete()

    delete_model.short_description = (
        "Delete selected License Profile and it's box files"
    )

    def sync_records(self, request, queryset):
        for record in queryset:
            insert_record_to_crm.delay(license_id=record.id, is_update=False)

    sync_records.short_description = "Insert Records To CRM"

    def update_records(self, request, queryset):
        for record in queryset:
            insert_record_to_crm.delay(license_id=record.id, is_update=True)

    update_records.short_description = "Update Records To CRM"

    def update_books_records(self, request, queryset):
        for record in queryset:
            create_customer_in_books_task.delay(license_id=record.id)

    update_books_records.short_description = "Update Records To Books"

    def refresh_integration_ids(self, request, queryset):
        for record in queryset:
            refresh_integration_ids_task.delay(license_id=record.id)

    refresh_integration_ids.short_description = "Refresh Integration IDs"

    def update_status_to_in_progress(self, request, queryset):
        for profile in queryset:
            profile.status = "in_progress"
            profile.save()
        messages.success(request, "Status Updated to in_progress!")

    update_status_to_in_progress.short_description = (
        "Revert Temporary approval/Update Status To in_progress"
    )
