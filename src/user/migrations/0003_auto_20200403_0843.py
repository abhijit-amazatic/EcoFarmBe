# Generated by Django 2.2 on 2020-04-03 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20200403_0831'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='date_of_birth',
            field=models.DateField(blank=True, db_index=True, default=None, null=True),
        ),
    ]
