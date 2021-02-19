from django.apps import apps
import random
from brand.permission_defaults import DEFAULT_ROLE_PERM


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