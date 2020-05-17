# Generated by Django 2.2 on 2020-05-15 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0024_auto_20200512_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='vendor_category',
            field=models.CharField(choices=[('cultivation', 'Cultivation'), ('nursery', 'Nursery'), ('testing', 'Testing'), ('healthcare', 'Healthcare'), ('patient', 'Patient'), ('investment', 'Investment'), ('ancillary services', 'Ancillary Services'), ('ancillary products', 'Anicllary Products'), ('hemp', 'Hemp'), ('brand', 'Brand'), ('event', 'Event'), ('processing', 'Processing'), ('distribution', 'Distribution'), ('manufacturing', 'Manufacturing'), ('retail', 'Retail')], max_length=60, verbose_name='Vendor Category'),
        ),
    ]