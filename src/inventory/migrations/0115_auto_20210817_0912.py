# Generated by Django 2.2 on 2021-08-17 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0114_auto_20210812_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominventory',
            name='cannabinoid_percentage',
            field=models.FloatField(blank=True, null=True, verbose_name='Cannabinoid Percentage'),
        ),
        migrations.AddField(
            model_name='custominventory',
            name='mfg_batch_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='MFG Batch ID'),
        ),
    ]
