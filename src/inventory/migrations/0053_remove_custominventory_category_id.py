# Generated by Django 2.2 on 2021-02-12 13:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0052_auto_20210210_1351'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='custominventory',
            name='category_id',
        ),
    ]
