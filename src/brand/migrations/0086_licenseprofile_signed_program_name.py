# Generated by Django 2.2 on 2021-08-06 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0085_remove_license_uploaded_resale_certificate_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseprofile',
            name='signed_program_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Signed Program Name'),
        ),
    ]
