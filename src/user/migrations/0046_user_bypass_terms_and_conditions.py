# Generated by Django 2.2 on 2021-02-22 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0045_user_internal_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='bypass_terms_and_conditions',
            field=models.BooleanField(default=False, verbose_name='Bypass Terms & Conditions Until this Flag is ON'),
        ),
    ]
