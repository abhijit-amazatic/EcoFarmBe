"""
Admin related customization.
"""
from django.contrib import admin
from django.db import models

from ..models import (
    License,
)
from import_export import resources


class LicenseResource(resources.ModelResource):
    class Meta:
        model = License
        fields = (
            "id",
            "status",
            "step",
            "legal_business_name",
            "license_profile__name",
            "license_profile__county",
            "license_profile__appellation",
            "brand__brand_name",
            "created_by__email",
            "organization__name",
            "client_id",
            "license_type",
            "owner_or_manager",
            "business_dba",
            "license_number",
            "expiration_date",
            "issue_date",
            "premises_address",
            "premises_county",
            "business_structure",
            "tax_identification",
            "ein_or_ssn",
            "premises_city",
            "zip_code",
            "premises_apn",
            "premises_state",
            "uploaded_license_to",
            "uploaded_sellers_permit_to",
            "uploaded_w9_to",
            "associated_program",
            "profile_category",
            "is_buyer",
            "is_seller",
            "is_updated_in_crm",
            "zoho_crm_id",
            "zoho_books_customer_ids",
            "zoho_books_vendor_ids",
            "is_data_fetching_complete",
            "status_before_expiry",
            "is_notified_before_expiry",
            "is_updated_via_trigger",
            "is_contract_downloaded",
            "crm_output",
            "books_output",
            "license_status",
            "created_on",
            "updated_on",
            "license_profile__region",
            "license_profile__ethics_and_certification",
            "license_profile__product_of_interest",
            "license_profile__cultivars_of_interest",
            "license_profile__signed_program_name",
            "license_profile__bank_account_number",
            "license_profile__bank_routing_number",
            "license_profile__bank_zip_code",
        )
        export_order = (
            "id",
            "status",
            "step",
            "legal_business_name",
            "license_profile__name",
            "license_profile__county",
            "license_profile__appellation",
            "brand__brand_name",
            "created_by__email",
            "organization__name",
            "client_id",
            "license_type",
            "owner_or_manager",
            "business_dba",
            "license_number",
            "expiration_date",
            "issue_date",
            "premises_address",
            "premises_county",
            "business_structure",
            "tax_identification",
            "ein_or_ssn",
            "premises_city",
            "zip_code",
            "premises_apn",
            "premises_state",
            "uploaded_license_to",
            "uploaded_sellers_permit_to",
            "uploaded_w9_to",
            "associated_program",
            "profile_category",
            "is_buyer",
            "is_seller",
            "is_updated_in_crm",
            "zoho_crm_id",
            "zoho_books_customer_ids",
            "zoho_books_vendor_ids",
            "is_data_fetching_complete",
            "status_before_expiry",
            "is_notified_before_expiry",
            "is_updated_via_trigger",
            "is_contract_downloaded",
            "crm_output",
            "books_output",
            "license_status",
            "created_on",
            "updated_on",
            "license_profile__region",
            "license_profile__ethics_and_certification",
            "license_profile__product_of_interest",
            "license_profile__cultivars_of_interest",
            "license_profile__signed_program_name",
            "license_profile__bank_account_number",
            "license_profile__bank_routing_number",
            "license_profile__bank_zip_code",
        )