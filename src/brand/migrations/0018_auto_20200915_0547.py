# Generated by Django 2.2 on 2020-09-15 05:47

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0017_auto_20200914_0558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cropoverview',
            name='overview',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(default=dict), default=list, size=None),
        ),
    ]
