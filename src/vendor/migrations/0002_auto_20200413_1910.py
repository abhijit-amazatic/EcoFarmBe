# Generated by Django 2.2 on 2020-04-13 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='vendor_categories',
            field=models.ManyToManyField(related_name='vendor_category', to='vendor.VendorCategory'),
        ),
    ]