# Generated by Django 2.2 on 2020-09-11 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0015_auto_20200911_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financialoverview',
            name='know_annual_budget',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]