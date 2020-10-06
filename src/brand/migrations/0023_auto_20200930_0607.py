# Generated by Django 2.2 on 2020-09-30 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0022_auto_20200924_0955'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='business_structure',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Business sructure'),
        ),
        migrations.AddField(
            model_name='license',
            name='ein_or_ssn',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='EIN or SSN'),
        ),
        migrations.AddField(
            model_name='license',
            name='tax_identification',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Tax Identification'),
        ),
    ]