# Generated by Django 2.2 on 2021-08-24 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0122_auto_20210819_1001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='category_name',
            field=models.CharField(choices=[('Flower - Tops', 'Flower - Tops'), ('Flower - Small', 'Flower - Small'), ('Trim', 'Trim'), ('Isolates - CBD', 'Isolates - CBD'), ('Isolates - THC', 'Isolates - THC'), ('Isolates - CBG', 'Isolates - CBG'), ('Isolates - CBN', 'Isolates - CBN'), ('Crude Oil - THC', 'Crude Oil - THC'), ('Crude Oil - CBD', 'Crude Oil - CBD'), ('Distillate Oil - THC', 'Distillate Oil - THC'), ('Distillate Oil - CBD', 'Distillate Oil - CBD'), ('Shatter', 'Shatter'), ('Sauce', 'Sauce'), ('Crumble', 'Crumble'), ('Kief', 'Kief'), ('Terpenes - Cultivar Specific', 'Terpenes - Cultivar Specific'), ('Terpenes - Cultivar Blended', 'Terpenes - Cultivar Blended'), ('Clones', 'Clones')], max_length=225, verbose_name='Item Category Name'),
        ),
    ]
