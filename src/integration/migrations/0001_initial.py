# Generated by Django 2.2 on 2020-04-15 05:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
                ('client_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='Client ID')),
                ('client_secret', models.CharField(blank=True, max_length=255, null=True, verbose_name='Client Secret')),
                ('access_token', models.CharField(max_length=255, verbose_name='Access Token')),
                ('refresh_token', models.CharField(max_length=255, verbose_name='Refresh Token')),
                ('access_expiry', models.DateTimeField(blank=True, null=True, verbose_name='Access Expiry')),
                ('refresh_expiry', models.DateTimeField(blank=True, null=True, verbose_name='Refresh Expiry')),
            ],
            options={
                'verbose_name': 'integration',
                'verbose_name_plural': 'integrations',
            },
        ),
    ]