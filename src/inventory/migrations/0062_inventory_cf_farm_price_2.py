# Generated by Django 2.2 on 2021-03-03 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0061_custominventory_client_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='cf_farm_price_2',
            field=models.FloatField(blank=True, null=True, verbose_name='Farm Price'),
        ),
    ]