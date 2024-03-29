# Generated by Django 2.2 on 2021-08-24 05:20

from django.db import migrations, models
from django.db.models import (F,)


def forward_func(apps, schema_editor):
    CustomInventoryVariable = apps.get_model("fee_variable", "CustomInventoryVariable")
    CustomInventoryVariable.objects.all().update(mcsp_fee_flower_smalls=F('mcsp_fee_flower_tops'))

def reverse_func(apps, schema_editor):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0016_auto_20210810_0958'),
    ]

    operations = [
        migrations.RenameField(
            model_name='custominventoryvariable',
            old_name='mcsp_fee_flowers',
            new_name='mcsp_fee_flower_tops',
        ),
        migrations.AlterField(
            model_name='custominventoryvariable',
            name='mcsp_fee_flower_tops',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='MCSP Fee - Flower Tops ($/lb)'),
        ),
        migrations.AddField(
            model_name='custominventoryvariable',
            name='mcsp_fee_flower_smalls',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='MCSP Fee - Flower Smalls ($/lb)'),
        ),
        migrations.RunPython(forward_func, reverse_code=reverse_func),
    ]
