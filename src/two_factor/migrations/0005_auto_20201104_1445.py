# Generated by Django 2.2 on 2020-11-04 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('two_factor', '0004_auto_20201020_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authyonetouchdevice',
            name='name',
            field=models.CharField(default='Push-Notifications Via Authy', help_text='The human-readable name of this device.', max_length=255),
        ),
    ]
