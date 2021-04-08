# Generated by Django 2.2 on 2021-04-07 08:47

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0075_auto_20210405_1530'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalinventory',
            name='cf_payment_method',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, default=list, null=True, size=None),
        ),
        migrations.AddField(
            model_name='inventory',
            name='cf_payment_method',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, default=list, null=True, size=None),
        ),
    ]