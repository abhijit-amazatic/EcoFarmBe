# Generated by Django 2.2 on 2020-05-23 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0020_auto_20200523_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.CharField(blank=True, choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('approved', 'Approved'), ('done', 'Done')], default='not_started', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='step',
            field=models.CharField(blank=True, default='0', max_length=255, null=True, verbose_name='Steps'),
        ),
    ]
