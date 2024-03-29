# Generated by Django 2.2 on 2021-11-26 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0141_auto_20211123_0844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='category_name',
            field=models.CharField(choices=[('Flower - Tops', 'Flower - Tops'), ('Flower - Small', 'Flower - Small'), ('Trim', 'Trim'), ('Isolates - CBD', 'Isolates - CBD'), ('Isolates - THC', 'Isolates - THC'), ('Isolates - CBG', 'Isolates - CBG'), ('Isolates - CBN', 'Isolates - CBN'), ('Crude Oil - THC', 'Crude Oil - THC'), ('Crude Oil - CBD', 'Crude Oil - CBD'), ('Distillate Oil - THC', 'Distillate Oil - THC'), ('Distillate Oil - CBD', 'Distillate Oil - CBD'), ('Hash', 'Hash'), ('Shatter', 'Shatter'), ('Sauce', 'Sauce'), ('Crumble', 'Crumble'), ('Kief', 'Kief'), ('Badder', 'Badder'), ('Live Resin', 'Live Resin'), ('Rosin', 'Rosin'), ('HTE', 'HTE'), ('Liquid Diamond Sauce', 'Liquid Diamond Sauce'), ('Terpenes - Cultivar Specific', 'Terpenes - Cultivar Specific'), ('Terpenes - Cultivar Blended', 'Terpenes - Cultivar Blended'), ('Clones', 'Clones')], max_length=225, verbose_name='Item Category Name'),
        ),
    ]
