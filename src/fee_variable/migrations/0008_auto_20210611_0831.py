# Generated by Django 2.2 on 2021-06-11 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0007_auto_20210330_0519'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominventoryvariable',
            name='mcsp_fee_per_g',
            field=models.CharField(blank=True, help_text='This fee will be used for Isolates, Concentrates and Terpenes', max_length=255, null=True, verbose_name='MCSP Fee (per gram)'),
        ),
        migrations.AddField(
            model_name='custominventoryvariable',
            name='mcsp_fee_per_pcs',
            field=models.CharField(blank=True, help_text='This fee will be used for Clones', max_length=255, null=True, verbose_name='MCSP Fee (per pcs)'),
        ),
        migrations.AlterField(
            model_name='custominventoryvariable',
            name='mcsp_fee',
            field=models.CharField(blank=True, help_text='This fee will be for Flowers and Trims', max_length=255, null=True, verbose_name='MCSP Fee (per lb)'),
        ),
    ]
