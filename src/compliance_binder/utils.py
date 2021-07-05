import json
import traceback

from integration.crm import get_record, parse_crm_record

from .models import BinderLicense

def sync_binder_license(record):
    """
    Webhook for Zoho CRM to sync License real time.
    """
    record = json.loads(record.dict()['response'])
    record = parse_crm_record('Licenses', [record])[0]
    try:
        binder_license_obj = BinderLicense.objects.get(license_number=record.get('license_number'))
    except BinderLicense.DoesNotExist:
        return False
    else:
        if not binder_license_obj.zoho_crm_id or binder_license_obj.zoho_crm_id == record.get('id'):
            if not binder_license_obj.profile_license:
                obj = binder_license_obj
                obj.premises_apn = record.get('premises_apn')
                obj.premises_address = record.get('premises_address')
                obj.premises_city = record.get('premises_city')
                obj.premises_county = record.get('premises_county')
                obj.premises_state = record.get('premises_state')
                obj.zip_code = record.get('zip_code')

            else:
                obj = binder_license_obj.profile_license
            try:
                # obj.license_number = record.get('license_number')
                obj.legal_business_name = record.get('legal_business_name')
                obj.license_type = record.get('license_type')
                # obj.profile_category = record.get('profile_category')

                obj.issue_date = record.get('issue_date')
                obj.expiration_date = record.get('expiration_date')
                obj.uploaded_license_to = record.get('uploaded_license_to')
                obj.uploaded_sellers_permit_to = record.get('uploaded_sellers_permit_to')
                obj.uploaded_w9_to = record.get('uploaded_w9_to')

                obj.license_status = record.get('license_status')
                if not obj.zoho_crm_id:
                    obj.zoho_crm_id = record.get('id')
                obj.is_updated_via_trigger = True
                obj.save()
                return True
            except Exception:
                traceback.print_exc()
    return False
