# Generated by Django 2.2 on 2021-08-11 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0110_auto_20210810_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='quantity_available',
            field=models.FloatField(verbose_name='Quantity Available'),
        ),
    ]