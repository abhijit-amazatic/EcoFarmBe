# Generated by Django 2.2 on 2020-12-02 08:17

from django.db import migrations

from brand.utils import get_unique_org_name

def rename_organization(apps, schema_editor):
    Organization = apps.get_model("brand", "Organization")
    for organization in Organization.objects.all():
        if organization.name == 'My Organization':
            organization.name = get_unique_org_name(Organization)
            organization.save()

def rename_organization_reverse(apps, schema_editor):
    Organization = apps.get_model("brand", "Organization")
    for organization in Organization.objects.all():
        if organization.name.startswith('My Organization '):
            organization.name = 'My Organization'
            organization.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0037_auto_20201201_0810'),
    ]

    operations = [
        migrations.RunPython(rename_organization, reverse_code=rename_organization_reverse),
    ]
