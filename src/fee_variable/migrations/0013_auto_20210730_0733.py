# Generated by Django 2.2 on 2021-07-30 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0012_auto_20210730_0655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventoryvariable',
            name='mcsp_fee_clones',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='This fee will be used for Clones', max_digits=6, null=True, verbose_name='MCSP Fee - Clones ($/pcs)'),
        ),
        migrations.AlterField(
            model_name='custominventoryvariable',
            name='mcsp_fee_concentrates_isolates_terpenes',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='This percentage will be used in MCSP Fee calculation for Concentrates, Isolates and Terpenes.', max_digits=6, null=True, verbose_name='MCSP Fee - Concentrates/Isolates/Terpenes (%)'),
        ),
        migrations.AlterField(
            model_name='custominventoryvariable',
            name='mcsp_fee_flowers_trims',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='This fee will be for Flowers and Trims.', max_digits=6, null=True, verbose_name='MCSP Fee - Flower/Trim ($/lb)'),
        ),
    ]