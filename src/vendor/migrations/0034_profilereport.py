# Generated by Django 2.2 on 2020-06-26 07:33

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0033_auto_20200527_0743'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_reports', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('vendor_profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile_report', to='vendor.VendorProfile', verbose_name='VendorProfile')),
            ],
        ),
    ]