# Generated by Django 2.2 on 2020-07-24 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0015_auto_20200723_0745'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountbasicprofile',
            name='county',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='County'),
        ),
    ]