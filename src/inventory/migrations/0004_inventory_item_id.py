# Generated by Django 2.2 on 2020-04-21 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_auto_20200421_0950'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='item_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Item ID'),
        ),
    ]
