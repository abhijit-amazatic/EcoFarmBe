# Generated by Django 2.2 on 2021-06-16 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0008_auto_20210611_0831'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorInventoryDefaultAccounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('zoho_organization', models.CharField(choices=[('efd', 'Thrive Society (EFD LLC)'), ('efl', 'Eco Farm Labs (EFL LLC)'), ('efn', 'Eco Farm Nursery (EFN LLC)')], max_length=20, unique=True, verbose_name='Zoho Organization')),
                ('sales_account', models.CharField(blank=True, max_length=255, null=True, verbose_name='Sales Account')),
                ('purchase_account', models.CharField(blank=True, max_length=255, null=True, verbose_name='Purchase Account')),
                ('inventory_account', models.CharField(blank=True, max_length=255, null=True, verbose_name='inventory Account')),
            ],
            options={
                'verbose_name': 'Vendor Inventory Default Accounts',
                'verbose_name_plural': 'Vendor Inventory Default Accounts',
            },
        ),
    ]
