# Generated by Django 2.2 on 2021-02-23 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0059_custominventory_procurement_rep'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominventory',
            name='payment_terms',
            field=models.CharField(blank=True, choices=[('60 Days', '60 Days'), ('21 Days', '21 Days')], max_length=50, null=True, verbose_name='Payment Terms'),
        ),
    ]