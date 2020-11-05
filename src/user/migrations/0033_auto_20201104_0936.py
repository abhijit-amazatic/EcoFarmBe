# Generated by Django 2.2 on 2020-11-04 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0032_auto_20201027_0623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('approved', 'Approved'), ('crop_overview', 'Crop Overview'), ('financial_overview', 'Financial Overview'), ('expired', 'Expired'), ('done', 'Done')], default='not_started', max_length=20),
        ),
    ]