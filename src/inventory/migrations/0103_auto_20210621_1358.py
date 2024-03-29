# Generated by Django 2.2 on 2021-06-21 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0102_auto_20210621_1044'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='cf_batch_qty_g',
            field=models.IntegerField(blank=True, null=True, verbose_name='Batch Quantity (g)'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='cf_trim_qty_lbs',
            field=models.FloatField(blank=True, null=True, verbose_name='Trim Quantity Used (lbs)'),
        ),
    ]
