# Generated by Django 2.2 on 2021-05-11 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0086_auto_20210510_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='marketplace_status',
            field=models.CharField(choices=[('Available', 'Available'), ('In-Testing', 'In-Testing'), ('Processing', 'Processing'), ('Flowering', 'Flowering'), ('Vegging', 'Vegging'), ('Rooting', 'Rooting')], default='In-Testing', max_length=225, verbose_name='Marketplace Status'),
        ),
    ]
