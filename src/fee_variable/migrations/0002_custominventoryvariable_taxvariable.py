# Generated by Django 2.2 on 2021-03-04 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomInventoryVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('tier', models.CharField(choices=[('gold', 'Gold'), ('silver', 'Silver'), ('bronze', 'Bronze')], max_length=255, verbose_name='Tier')),
                ('program_type', models.CharField(choices=[('ifp', 'IFP Program'), ('ibp', 'IBP Program')], max_length=255, verbose_name='Program Type')),
                ('mcsp_fee', models.CharField(blank=True, max_length=255, null=True, verbose_name='MCSP Fee')),
            ],
            options={
                'verbose_name': 'Custom Inventory Variable',
                'verbose_name_plural': 'Custom Inventory Variables',
            },
        ),
        migrations.CreateModel(
            name='TaxVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('cultivar_tax', models.CharField(blank=True, max_length=255, null=True, verbose_name='Cultivar Tax')),
                ('trim_tax', models.CharField(blank=True, max_length=255, null=True, verbose_name='Trim Tax')),
            ],
            options={
                'verbose_name': 'Tax Variable',
                'verbose_name_plural': 'Tax Variables',
            },
        ),
    ]
