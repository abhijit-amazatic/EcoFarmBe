# Generated by Django 2.2 on 2020-12-21 05:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0042_documents_thumbnail_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='inventory_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Inventory Name'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='parent_category_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Parent Category Name'),
        ),
    ]
