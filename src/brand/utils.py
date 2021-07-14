import random
from django.apps import apps

from integration.crm import get_crm_obj
from brand.permission_defaults import DEFAULT_ROLE_PERM
from .models import LicenseProfile

def get_unique_org_name(organization_model):
    name = f'My Organization {int(random.random()*100000):05}'
    if not organization_model.objects.filter(name=name).exists():
        return name
    return get_unique_org_name(organization_model)

def add_default_organization_role():
    Organization = apps.get_model('brand', 'Organization')
    OrganizationRole = apps.get_model('brand', 'OrganizationRole')
    for org in Organization.objects.all():
        for role_name, perms_ls in DEFAULT_ROLE_PERM.items():
            role, _ = OrganizationRole.objects.get_or_create(
                organization=org,
                name=role_name,
            )
            role.permissions.set(perms_ls)
            role.save()

def fetch_account_owners(qs=None, offset=0):
    if not qs:
        qs = LicenseProfile.objects.all()
        qs.filter(zoho_crm_account_id='').update(
            crm_account_owner_id='',
            crm_account_owner_email='',
        )
        qs.filter(zoho_crm_account_id__isnull=True).update(
            crm_account_owner_id='',
            crm_account_owner_email='',
        )

    account_ids = ','.join([id for id in qs.values_list('zoho_crm_account_id', flat=True) if id])
    crm_obj = get_crm_obj()
    query = (
        f"SELECT id,Owner.email,Owner.id FROM Accounts WHERE id in ({account_ids}) LIMIT 200 OFFSET {offset}"
    )
    resp = crm_obj.get_coql_query(query=query)
    if resp is not None:
        if resp.get('status_code') == 200:
            data = resp.get('data', [])
            for account in data:
                qs.filter(zoho_crm_account_id=account.get('id')).update(
                    crm_account_owner_id=account.get('Owner.id'),
                    crm_account_owner_email=account.get('Owner.email'),
                )
            if resp.get('info', {}).get('more_records'):
                fetch_account_owners(qs=qs, offset=offset+200)
        else:
            print(resp)

def fetch_vendor_owners(qs=None, offset=0):
    if not qs:
        qs = LicenseProfile.objects.all()
        qs.filter(zoho_crm_vendor_id__isnull='').update(
            crm_vendor_owner_id='',
            crm_vendor_owner_email='',
        )
        qs.filter(zoho_crm_vendor_id__isnull=True).update(
            crm_vendor_owner_id='',
            crm_vendor_owner_email='',
        )
    vendor_ids = ','.join([id for id in qs.values_list('zoho_crm_vendor_id', flat=True) if id])
    crm_obj = get_crm_obj()
    query = (
        f"SELECT id,Owner.email,Owner.id FROM Vendors WHERE id in ({vendor_ids}) LIMIT 200 OFFSET {offset}"
    )
    resp = crm_obj.get_coql_query(query=query)
    if resp is not None:
        if resp.get('status_code') == 200:
            data = resp.get('data', [])
            for vendor in data:
                qs.filter(zoho_crm_vendor_id=vendor.get('id')).update(
                    crm_vendor_owner_id=vendor.get('Owner.id'),
                    crm_vendor_owner_email=vendor.get('Owner.email'),
                )
            if resp.get('info', {}).get('more_records'):
                fetch_vendor_owners(qs=qs, offset=offset+200)
        else:
            print(resp)