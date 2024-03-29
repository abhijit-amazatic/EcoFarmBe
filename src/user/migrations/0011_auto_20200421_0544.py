# Generated by Django 2.2 on 2020-04-21 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_auto_20200417_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='business_dba',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Business DBA'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_approved',
            field=models.BooleanField(default=False, verbose_name='Approve User'),
        ),
        migrations.AlterField(
            model_name='user',
            name='legal_business_name',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Legal Business Name'),
        ),
    ]
