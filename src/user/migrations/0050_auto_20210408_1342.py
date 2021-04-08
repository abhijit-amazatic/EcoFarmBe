# Generated by Django 2.2 on 2021-04-08 13:42

from django.db import migrations, models
import user.models

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0049_auto_20210408_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='unique_user_id',
            field=models.CharField(default=user.models.generate_unique_user_id, max_length=255, unique=True, verbose_name='Unique User Id'),
        ),
    ]
