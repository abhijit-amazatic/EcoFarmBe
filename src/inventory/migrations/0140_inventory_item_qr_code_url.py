# Generated by Django 2.2 on 2021-11-18 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0139_auto_20211118_0844'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='item_qr_code_url',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='QR code-Detailed Item View'),
        ),
    ]
