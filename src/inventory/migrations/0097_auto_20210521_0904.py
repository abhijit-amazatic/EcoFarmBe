# Generated by Django 2.2 on 2021-05-21 09:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0096_summary_vendor_vendordailysummary'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vendor',
            options={'verbose_name': 'Vendor', 'verbose_name_plural': 'Vendor Wise Summary'},
        ),
        migrations.AlterModelOptions(
            name='vendordailysummary',
            options={'verbose_name': 'Vendor Daily Summary', 'verbose_name_plural': 'Vendor Daily Summary'},
        ),
    ]