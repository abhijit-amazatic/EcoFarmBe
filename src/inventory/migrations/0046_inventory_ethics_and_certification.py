# Generated by Django 2.2 on 2021-01-19 07:45

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0045_inventory_nutrients'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='ethics_and_certification',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, default=list, null=True, size=None),
        ),
    ]