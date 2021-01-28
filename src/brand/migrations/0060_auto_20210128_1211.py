# Generated by Django 2.2 on 2021-01-28 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0059_auto_20210128_0955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onboardingdatafetch',
            name='data_fetch_status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('licence_data_not_found', 'Licence Data Not Found'), ('licence_association_not_found', 'Licence Association Not Found'), ('fetched', 'Fetched'), ('complete', 'Complete'), ('error', 'Error')], default='not_started', max_length=255, verbose_name='Data From CRM Status'),
        ),
    ]
