# Generated by Django 2.2.3 on 2019-08-01 15:29

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, unique=True, verbose_name='Email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='website_url',
            field=models.CharField(max_length=255, null=True, unique=True, validators=[core.validators.full_domain_validator], verbose_name='Website URL'),
        ),
    ]
