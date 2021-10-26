# Generated by Django 2.2 on 2021-10-26 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0127_auto_20211011_1322'),
    ]

    operations = [
        migrations.AddField(
            model_name='documents',
            name='S3_mobile_url',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Mobile Url'),
        ),
        migrations.AddField(
            model_name='documents',
            name='S3_url',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Box Url'),
        ),
        migrations.AddField(
            model_name='documents',
            name='s3_thumbnail_url',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Thumbnail Url'),
        ),
    ]
