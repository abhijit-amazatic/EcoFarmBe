# Generated by Django 2.2 on 2020-12-28 05:31

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brand', '0041_auto_20201223_1301'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationUserInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('full_name', models.CharField(max_length=200, verbose_name='Full Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Email Address')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, verbose_name='Phone')),
                ('is_accepted', models.BooleanField(default=False, verbose_name='Is Accepted')),
                ('is_completed', models.BooleanField(default=False, verbose_name='Is Completed')),
                ('expires_at', models.DateTimeField(default=datetime.datetime(2020, 12, 30, 5, 31, 43, 998290, tzinfo=utc))),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invited_users', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('licenses', models.ManyToManyField(blank=True, to='brand.License', verbose_name='Licenses')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='brand.Organization', verbose_name='Organization')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='brand.OrganizationRole', verbose_name='Organization Role')),
            ],
            options={
                'verbose_name': 'Organization User Invite',
                'verbose_name_plural': 'Organization User Invites',
            },
        ),
    ]