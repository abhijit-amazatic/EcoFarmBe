# Generated by Django 2.2 on 2021-08-17 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0115_auto_20210817_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominventory',
            name='cultivar_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Cultivar Name'),
        ),
        migrations.AddField(
            model_name='custominventory',
            name='cultivar_crm_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Cultivar CRM ID'),
        ),
    ]