# Generated by Django 2.2 on 2020-07-16 07:00

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0019_auto_20200715_0418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='documents',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, null=True, size=None),
        ),
    ]