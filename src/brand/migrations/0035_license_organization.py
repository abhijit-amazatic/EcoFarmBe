# Generated by Django 2.2 on 2020-11-27 07:53
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
def create_organization(apps, schema_editor):
    User = apps.get_model("user", "User")
    Organization = apps.get_model("brand", "Organization")
    for user in User.objects.all():
        Organization.objects.get_or_create(
            name='My Organization',
            created_by=user,
        )

def create_organization_reverse(apps, schema_editor):
    pass


def Add_license_organization(apps, schema_editor):
    License = apps.get_model("brand", "License")
    Organization = apps.get_model("brand", "Organization")
    for license in License.objects.all():
        organization, _ = Organization.objects.get_or_create(
            name='My Organization',
            created_by=license.created_by,
        )
        license.organization = organization
        license.save()

def Add_license_organization_reverse(apps, schema_editor):
    # pass
    License = apps.get_model("brand", "License")
    Organization = apps.get_model("brand", "Organization")
    for license in License.objects.all():
        organization = Organization.objects.get(id=license.organization_id)
        license.created_by_id = organization.created_by_id
        license.save()

class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0034_license_is_updated_via_trigger'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, verbose_name='Organization Name')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organizations', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
            ],
            options={
                'verbose_name': 'Organization',
                'verbose_name_plural': 'Organizations',
                'unique_together': {('name', 'created_by')},
            },
        ),
        migrations.RunPython(create_organization, reverse_code=create_organization_reverse),
        migrations.AddField(
            model_name='license',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='licenses', to='brand.Organization', verbose_name='Organization'),
        ),
        migrations.AlterField(
            model_name='license',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.RunPython(Add_license_organization, reverse_code=Add_license_organization_reverse),
        migrations.AlterField(
            model_name='license',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='licenses', to='brand.Organization', verbose_name='Organization'),
        ),
        migrations.RemoveField(
            model_name='license',
            name='created_by',
        ),
    ]
