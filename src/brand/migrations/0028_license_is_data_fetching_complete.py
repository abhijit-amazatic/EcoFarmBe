# Generated by Django 2.2 on 2020-11-05 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0027_auto_20201105_0639'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='is_data_fetching_complete',
            field=models.BooleanField(default=False, verbose_name='Is crm data fetched for existing user'),
        ),
    ]