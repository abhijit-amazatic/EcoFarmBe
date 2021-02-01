# Generated by Django 2.2 on 2021-01-28 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0002_integration_expiry_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_type', models.CharField(choices=[('gold', 'Gold'), ('silver', 'Silver')], max_length=255, verbose_name='Program')),
                ('mcsp_fee', models.CharField(blank=True, max_length=255, null=True, verbose_name='MCSP Fee(%)')),
                ('net_7_14', models.CharField(blank=True, max_length=255, null=True, verbose_name='Net 7-14(%)')),
                ('net_14_30', models.CharField(blank=True, max_length=255, null=True, verbose_name='Net 14-30(%)')),
                ('cash', models.CharField(blank=True, max_length=255, null=True, verbose_name='Cash(%)')),
                ('transportation_fee', models.CharField(blank=True, max_length=255, null=True, verbose_name='Transportation Fee/Mile($)')),
            ],
            options={
                'verbose_name': 'Order Variable',
            },
        ),
    ]