# Generated by Django 2.2 on 2021-11-30 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0108_auto_20211126_0711'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseprofile',
            name='is_confia_member',
            field=models.BooleanField(default=False, verbose_name='Is Confia Member/Signed Up'),
        ),
    ]
