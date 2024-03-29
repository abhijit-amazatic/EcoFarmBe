# Generated by Django 2.2 on 2021-06-21 10:44

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0101_inventory_cf_trim_qty_lbs'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitemedit',
            name='cultivar_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Cultivar Name'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='item_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='item_data'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='sku',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='SKU'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='vendor_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Vendor Name'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='zoho_item_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Zoho Item ID'),
        ),
    ]
