# Generated by Django 2.2 on 2020-04-14 06:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_auto_20200407_0957'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(blank=True, choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default=None, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='step',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Steps'),
        ),
    ]
