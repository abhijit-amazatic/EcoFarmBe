# Generated by Django 2.2 on 2021-07-05 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0077_license_is_notified_before_expiry'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='license_status',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
