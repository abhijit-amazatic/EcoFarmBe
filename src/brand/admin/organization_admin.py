"""
Admin related customization.
"""
from django.contrib import admin
from django.db import models
from django.contrib.admin import widgets
from django.utils import timezone

import nested_admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

from ..models import (
    Organization,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserRole,
)


class OrganizationRoleNestedAdmin(nested_admin.NestedTabularInline):
    """
    OrganizationRoleAdmin
    """

    extra = 0
    model = OrganizationRole
    readonly_fields = (
        "created_on",
        "updated_on",
    )
    formfield_overrides = {
        # models.ManyToManyField: {'widget': PermissionSelectMultipleWidget()},
        models.ManyToManyField: {
            "widget": widgets.FilteredSelectMultiple("Permission", is_stacked=False)
        },
    }


class OrganizationUserRoleNestedAdmin(nested_admin.NestedTabularInline):
    extra = 0
    model = OrganizationUserRole
    readonly_fields = (
        "created_on",
        "updated_on",
    )
    formfield_overrides = {
        models.ManyToManyField: {
            "widget": widgets.FilteredSelectMultiple("Permission", is_stacked=False)
        },
    }

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "role":
            if request._organization is not None:
                field.queryset = field.queryset.filter(
                    organization=request._organization
                )
            else:
                field.queryset = field.queryset.none()
        return field

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == "licenses":
            if request._organization is not None:
                field.queryset = field.queryset.filter(
                    organization=request._organization
                )
            else:
                field.queryset = field.queryset.none()
        return field

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
        return formfield


class OrganizationUserNestedAdmin(nested_admin.NestedTabularInline):
    extra = 0
    model = OrganizationUser
    readonly_fields = (
        "created_on",
        "updated_on",
    )
    inlines = [OrganizationUserRoleNestedAdmin]


class OrganizationResource(resources.ModelResource):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "created_by__email",
            "zoho_crm_id",
            "is_updated_in_crm",
            "email",
            "phone",
            "category",
            "about",
            "ethics_and_certifications",
            "created_on",
            "updated_on",
        )


class OrganizationAdmin(ExportActionMixin, nested_admin.NestedModelAdmin):
    """
    Configuring brand
    """

    model = Organization
    list_display = (
        "name",
        "created_by",
        "created_on",
        "updated_on",
    )
    search_fields = (
        "name",
        "created_by__email",
    )
    list_filter = (
        ("created_on", DateRangeFilter),
        ("updated_on", DateRangeFilter),
    )
    ordering = (
        "-created_on",
        "updated_on",
    )
    inlines = [OrganizationRoleNestedAdmin, OrganizationUserNestedAdmin]
    resource_class = OrganizationResource

    def get_form(self, request, obj=None, **kwargs):
        request._organization = obj
        return super().get_form(request, obj, **kwargs)


class OrganizationRoleAdmin(admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """

    readonly_fields = (
        "created_on",
        "updated_on",
    )

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": widgets.FilteredSelectMultiple("Permission", is_stacked=False)
        },
    }
