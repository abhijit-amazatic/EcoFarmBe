# Generated by Django 2.2 on 2022-01-05 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0009_auto_20220105_1040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confiacallback',
            name='confia_member_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='confia Member ID'),
        ),
        migrations.AlterField(
            model_name='confiacallback',
            name='partner_company_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='client ID'),
        ),
    ]