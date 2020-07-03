# Generated by Django 2.2 on 2020-07-03 06:11

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0034_profilereport'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilereport',
            name='profile_type',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255), blank=True, default=list, null=True, size=None),
        ),
    ]
