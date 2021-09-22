# Generated by Django 2.2 on 2021-08-27 07:54

import brand.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0092_auto_20210826_1458'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='client_id',
            field=models.PositiveIntegerField(help_text='Randomly genrated 6 digit number.', null=True, validators=[brand.models.client_id_validator]),
        ),
    ]