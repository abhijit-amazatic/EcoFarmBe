# Generated by Django 2.2 on 2020-05-14 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_inventory_cf_cbd'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='cf_cfi_published',
            field=models.BooleanField(default=None, verbose_name='CFI_Published'),
            preserve_default=False,
        ),
    ]
