# Generated by Django 2.2 on 2020-09-22 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0027_itemfeedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemfeedback',
            name='estimate_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Estimate Number'),
        ),
        migrations.AlterField(
            model_name='itemfeedback',
            name='item',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='item_id'),
        ),
    ]
