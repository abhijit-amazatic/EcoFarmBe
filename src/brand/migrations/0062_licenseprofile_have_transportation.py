# Generated by Django 2.2 on 2021-02-18 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0061_organizationuser_is_disabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseprofile',
            name='have_transportation',
            field=models.BooleanField(blank=True, null=True, verbose_name='Have Transportation'),
        ),
    ]