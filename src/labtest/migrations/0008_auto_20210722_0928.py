# Generated by Django 2.2 on 2021-07-22 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labtest', '0007_auto_20210722_0650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='labtest',
            name='Total_Terpenes',
            field=models.FloatField(default=0.0, max_length=255, verbose_name='Total_Terpenes'),
        ),
    ]
