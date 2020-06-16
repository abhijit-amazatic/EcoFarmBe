# Generated by Django 2.2 on 2020-06-12 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_inventory_cultivar'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='cf_farm_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Farm Price'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_next_harvest_date',
            field=models.DateTimeField(default=None),
        ),
    ]