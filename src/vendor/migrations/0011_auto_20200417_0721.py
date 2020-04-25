# Generated by Django 2.2 on 2020-04-17 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0010_processingoverview'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='license',
            name='premises_country',
        ),
        migrations.AddField(
            model_name='license',
            name='premises_county',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Premises County'),
        ),
    ]