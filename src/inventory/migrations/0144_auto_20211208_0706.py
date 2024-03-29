# Generated by Django 2.2 on 2021-12-08 07:06

import core.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0143_auto_20211207_0322'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitemedit',
            name='biomass_input_g',
            field=core.db.models.fields.PositiveDecimalField(blank=True, decimal_places=6, help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.', max_digits=16, null=True, verbose_name='Raw Material Input (grams)'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='biomass_type',
            field=models.CharField(blank=True, choices=[('Unknown', 'Unknown'), ('Dried Flower', 'Dried Flower'), ('Dried Leaf', 'Dried Leaf'), ('Fresh Plant', 'Fresh Plant')], max_length=50, null=True, verbose_name='Biomass Type'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='cultivation_tax',
            field=core.db.models.fields.PositiveDecimalField(blank=True, decimal_places=6, max_digits=16, null=True, verbose_name='Cultivation Tax'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='mcsp_fee',
            field=core.db.models.fields.PositiveDecimalField(blank=True, decimal_places=6, max_digits=16, null=True, verbose_name='MCSP Fee'),
        ),
        migrations.AddField(
            model_name='inventoryitemedit',
            name='total_batch_quantity',
            field=core.db.models.fields.PositiveDecimalField(blank=True, decimal_places=6, help_text='This field is used to calculate tax for Isolates, Concentrates and Terpenes.', max_digits=16, null=True, verbose_name='Total Batch Output'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='cf_raw_material_input_g',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=16, null=True, verbose_name='Biomass Input (grams)'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='manufacturer',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Manufacturer'),
        ),
    ]
