# Generated by Django 2.2 on 2021-01-12 10:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0053_auto_20210112_0848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='brand',
            name='brand_image',
        ),
    ]
