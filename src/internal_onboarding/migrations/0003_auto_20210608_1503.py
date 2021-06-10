# Generated by Django 2.2 on 2021-06-08 15:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('internal_onboarding', '0002_auto_20210602_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='completed_on',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Completed On'),
        ),
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='is_user_created',
            field=models.BooleanField(default=False, verbose_name='Is User Created'),
        ),
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='is_user_do_onboarding',
            field=models.BooleanField(default=False, verbose_name='Is User Do Onboarding'),
        ),
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='license',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboarding_invites', to='brand.License', verbose_name='License'),
        ),
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='roles',
            field=models.ManyToManyField(related_name='internal_onboarding_invites', to='brand.OrganizationRole', verbose_name='Roles'),
        ),
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('completed', 'Completed')], default='pending', max_length=60),
        ),
        migrations.AlterField(
            model_name='internalonboardinginvite',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboarding_invites', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]