# Generated by Django 2.2 on 2020-04-14 18:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0008_auto_20200414_1828'),
    ]

    operations = [
        migrations.AlterField(
            model_name='license',
            name='vendor_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vendor.VendorProfile', verbose_name='VendorProfile'),
        ),
    ]