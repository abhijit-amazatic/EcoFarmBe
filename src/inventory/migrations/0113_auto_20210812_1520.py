# Generated by Django 2.2 on 2021-08-12 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0112_auto_20210811_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='days_to_prepare_clones',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Rooting Days'),
        ),
    ]