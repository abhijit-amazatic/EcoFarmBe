# Generated by Django 2.2 on 2020-04-25 11:51

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0019_auto_20200425_0616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financialoverview',
            name='financial_details',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='processingoverview',
            name='processing_config',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='profileoverview',
            name='profile_overview',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='programoverview',
            name='program_details',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]