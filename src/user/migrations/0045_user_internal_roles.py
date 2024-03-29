# Generated by Django 2.2 on 2021-02-19 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('permission', '0003_remove_internalrole_users'),
        ('user', '0044_helpdocumentation_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='internal_roles',
            field=models.ManyToManyField(blank=True, related_name='users', to='permission.InternalRole', verbose_name='Internal Roles'),
        ),
    ]
