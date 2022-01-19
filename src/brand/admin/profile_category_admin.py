"""
Admin related customization.
"""
from django.contrib import admin

import nested_admin

from ..models import (
    ProfileCategory,
)

from fee_variable.models import ProgramProfileCategoryAgreement


class ProgramProfileCategoryAgreementInline(nested_admin.NestedTabularInline):
    extra = 0
    model = ProgramProfileCategoryAgreement
    readonly_fields = (
        "created_on",
        "updated_on",
    )



class ProfileCategoryAdmin(nested_admin.NestedModelAdmin):
    """
    ProfileCategoryAdmin
    """
    inlines = [ProgramProfileCategoryAgreementInline]
    #search_fields = ('',)

    def get_form(self, request, obj=None, **kwargs):
        request._profile_category = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "default_program":
            if request._profile_category is not None:
                field.queryset = field.queryset.filter(
                    program_profile_category_agreement_set__profile_category=request._profile_category
                )
            else:
                field.queryset = field.queryset.none()
        return field

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield:
            if db_field.name == "default_program":
                formfield.widget.can_add_related = False
                formfield.widget.can_change_related = False
                formfield.widget.can_delete_related = False
        return formfield
