# Generated by Django 2.2 on 2021-08-18 06:12

import core.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0120_auto_20210817_1140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='cannabinoid_percentage',
            field=core.db.models.fields.PercentField(blank=True, null=True, verbose_name='Cannabinoid Percentage'),
        ),
    ]