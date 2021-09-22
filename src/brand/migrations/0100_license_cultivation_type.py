# Generated by Django 2.2 on 2021-09-16 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0099_auto_20210915_1245'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='cultivation_type',
            field=models.CharField(blank=True, choices=[('Mixed-Light', 'Mixed-Light'), ('Outdoor', 'Outdoor'), ('Indoor', 'Indoor')], max_length=255, null=True, verbose_name='Cultivation Type'),
        ),
    ]