# Generated by Django 2.2 on 2021-08-12 15:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0113_auto_20210812_1520'),
    ]

    operations = [
        migrations.RenameField(
            model_name='custominventory',
            old_name='days_to_prepare_clones',
            new_name='rooting_days',
        ),
    ]
