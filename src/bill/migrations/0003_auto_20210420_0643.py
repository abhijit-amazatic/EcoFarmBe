# Generated by Django 2.2 on 2021-04-20 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bill', '0002_auto_20210420_0610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='estimate',
            name='sub_total',
            field=models.FloatField(blank=True, null=True, verbose_name='Subtotal'),
        ),
    ]
