# Generated by Django 2.2 on 2021-03-09 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0063_auto_20210303_1049'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominventory',
            name='crm_vendor_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='CRM Vendor ID'),
        ),
    ]