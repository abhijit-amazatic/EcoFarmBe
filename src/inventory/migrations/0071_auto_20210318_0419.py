# Generated by Django 2.2 on 2021-03-18 04:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0070_auto_20210317_1329'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='county',
            options={'verbose_name': 'Inventory County', 'verbose_name_plural': 'County Wise Summary'},
        ),
    ]
