# Generated by Django 2.2 on 2021-05-06 07:11

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0070_sign_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='NurseryOverview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nursery_sqf', models.IntegerField(blank=True, null=True, verbose_name='Nursary Sqf')),
                ('weekly_productions', models.IntegerField(blank=True, null=True, verbose_name='Weekly Productions')),
                ('clones_per_productions', models.IntegerField(blank=True, null=True, verbose_name='clones Per Productions')),
                ('types_of_nutrients', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255), blank=True, default=list, null=True, size=None)),
                ('growing_medium', models.CharField(blank=True, max_length=255, null=True, verbose_name='Growing Medium')),
                ('lighting_type', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255), blank=True, default=list, null=True, size=None)),
                ('cultivars_in_production', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255), blank=True, default=list, null=True, size=None)),
                ('minimun_order_qty', models.IntegerField(blank=True, null=True, verbose_name='clones Per Productions')),
                ('order_hold_days', models.IntegerField(blank=True, null=True, verbose_name='clones Per Productions')),
                ('is_draft', models.BooleanField(default=False, verbose_name='Is Draft')),
                ('license', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='nursery_overview', to='brand.License', verbose_name='License')),
            ],
        ),
    ]