# Generated by Django 2.2 on 2021-10-11 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0125_inventory_client_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='vendor_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Vendor ID'),
        ),
    ]
