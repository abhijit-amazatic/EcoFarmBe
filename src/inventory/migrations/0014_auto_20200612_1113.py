# Generated by Django 2.2 on 2020-06-12 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0013_auto_20200612_1107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='cf_next_harvest_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]