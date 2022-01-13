"""
All periodic tasks related to brand.
"""
import traceback
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from celery.task import periodic_task
from django.utils import timezone

from core.celery import app

from integration.crm import (
    get_licenses,
    get_record,
    get_format_dict,
    get_records_from_crm,
    search_query,
    insert_records,
    get_associated_vendor_from_license,
    get_associated_account_from_license,
    get_crm_vendor_to_db,
    get_crm_account_to_db,
    get_license_by_clint_id,
    get_vendor_by_clint_id,
    get_account_by_clint_id,
    get_crm_license,
    get_crm_license_by_id
)
from integration.books import (
    get_books_obj,
)

from ..models import (
    License,
)
from .create_customer_in_books import create_customer_in_books_task


@app.task(queue="general")
def refresh_integration_ids_task(license_id=None):
    """
    Populate Integration records id to respective fields.
    """
    if license_id:
        qs = License.objects.filter(id=license_id)
    else:
        qs = License.objects.filter(status__in=('approved', 'completed'))
    for license_obj in qs:
        license_dict = {}

        if license_obj.zoho_crm_id:
            license_dict = get_crm_license_by_id(license_obj.zoho_crm_id)
        if not license_dict:
            license_dict = get_license_by_clint_id(license_obj.client_id)
        if not license_dict:
            license_dict = get_licenses(license_obj.legal_business_name, license_obj.license_number)
        if not license_dict:
            license_dict = get_crm_license(license_obj.license_number)

        if license_dict and license_dict.get('id'):
            license_obj.zoho_crm_id = license_dict.get('id')
            license_obj.save()
        else:
            print(f"License {license_obj.license_number} not found on crm.")

        if license_obj.zoho_crm_id:
            # if not license_dict:
            #     response = get_record(module='Licenses', record_id=license_obj.zoho_crm_id, full=True)
            #     if response.get('status_code') == 200:
            #         license_dict = response.get('response')
            #     else:
            #         print(response)

            if license_dict:
                try:
                    license_profile = license_obj.license_profile
                except ObjectDoesNotExist:
                    pass
                else:
                    vendor_id = get_vendor_by_clint_id(license_obj.client_id).get('id')
                    # if not vendor_id:
                    #     vendor_id = get_associated_vendor_from_license(license_dict)
                    license_profile.zoho_crm_account_id = vendor_id
                    if vendor_id:
                        vendor_dict = get_crm_vendor_to_db(vendor_id)
                        if vendor_dict:
                            vendor_owner = vendor_dict.get('Owner') or {}
                            license_profile.crm_vendor_owner_id = vendor_owner.get('id'),
                            license_profile.crm_vendor_owner_email = vendor_owner.get('email'),

                    account_id = get_account_by_clint_id(license_obj.client_id).get('id')
                    # if not account_id:
                    #     account_id = get_associated_account_from_license(license_dict)
                    license_profile.zoho_crm_account_id = account_id
                    if account_id:
                        account_dict = get_crm_account_to_db(account_id)
                        if account_dict:
                            account_owner = account_dict.get('Owner') or {}
                            license_profile.crm_account_owner_id = account_owner.get('id'),
                            license_profile.crm_account_owner_email = account_owner.get('email'),
                    license_profile.save()
                create_customer_in_books_task.delay(license_obj.id)
    return None
