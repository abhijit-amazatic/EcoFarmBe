# Generated by Django 2.2 on 2021-02-19 10:40

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('permission', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='internalrole',
            name='users',
            field=models.ManyToManyField(blank=True, related_name='internal_roles', to=settings.AUTH_USER_MODEL, verbose_name='Users'),
        ),
    ]
