# Generated by Django 2.2 on 2021-08-26 14:58

import django.contrib.postgres.fields.hstore
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0091_remove_licenseprofile_zoho_crm_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='license',
            name='zoho_books_customer_id_old',
        ),
        migrations.RemoveField(
            model_name='license',
            name='zoho_books_vendor_id_old',
        ),
        migrations.AlterField(
            model_name='license',
            name='zoho_books_customer_ids',
            field=django.contrib.postgres.fields.hstore.HStoreField(blank=True, default=dict, verbose_name='Zoho Books Customer IDs'),
        ),
        migrations.AlterField(
            model_name='license',
            name='zoho_books_vendor_ids',
            field=django.contrib.postgres.fields.hstore.HStoreField(blank=True, default=dict, verbose_name='Zoho Books Vendor IDs'),
        ),
    ]