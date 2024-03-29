# Generated by Django 2.2 on 2020-06-03 06:30

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cultivar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cultivar_crm_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='Cultivar ID')),
                ('cultivar_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Cultivar Name')),
                ('cultivar_type', models.CharField(blank=True, max_length=50, null=True, verbose_name='Cultivar Type')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('thc_range', models.FloatField(blank=True, null=True, verbose_name='THC')),
                ('cbd_range', models.FloatField(blank=True, null=True, verbose_name='CBD')),
                ('cbg_range', models.FloatField(blank=True, null=True, verbose_name='CBG')),
                ('thcv_range', models.FloatField(blank=True, null=True, verbose_name='THCv')),
                ('flavor', models.CharField(blank=True, max_length=255, null=True, verbose_name='Flavor')),
                ('effect', models.CharField(blank=True, max_length=255, null=True, verbose_name='Effect')),
                ('terpenes_primary', models.CharField(blank=True, max_length=255, null=True, verbose_name='Terpenes_Primary')),
                ('terpenes_secondary', models.CharField(blank=True, max_length=255, null=True, verbose_name='Terpenes_Secondary')),
                ('parent_1', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, null=True, size=None)),
                ('parent_2', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, null=True, size=None)),
                ('cultivar_image', models.URLField(blank=True, max_length=255, null=True, verbose_name='Image')),
                ('lab_test_crm_id', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, null=True, size=None)),
            ],
        ),
    ]
