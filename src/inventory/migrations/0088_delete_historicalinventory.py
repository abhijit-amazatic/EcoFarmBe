# Generated by Django 2.2 on 2021-05-12 06:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0087_auto_20210511_1540'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HistoricalInventory',
        ),
    ]
