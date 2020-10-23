# Generated by Django 2.2 on 2020-10-23 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0030_auto_20201020_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='alternate_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Alternate Email address'),
        ),
        migrations.AddField(
            model_name='user',
            name='recovery_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Recovery Email address'),
        ),
    ]
