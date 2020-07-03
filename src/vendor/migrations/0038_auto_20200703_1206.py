# Generated by Django 2.2 on 2020-07-03 12:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vendor', '0037_auto_20200703_0742'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilereport',
            name='user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Report Manager'),
        ),
        migrations.AlterField(
            model_name='profilereport',
            name='vendor_profile',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Vendor Profile'),
        ),
    ]
