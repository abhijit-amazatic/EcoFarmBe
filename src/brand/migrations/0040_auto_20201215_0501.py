# Generated by Django 2.2 on 2020-12-15 05:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0039_organizationrole_organizationuser_organizationuserrole_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='is_updated_in_crm',
            field=models.BooleanField(default=False, verbose_name='Is Updated In CRM'),
        ),
        migrations.AddField(
            model_name='organization',
            name='zoho_crm_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Zoho CRM ID'),
        ),
    ]