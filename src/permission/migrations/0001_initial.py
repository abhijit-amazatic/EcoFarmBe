# Generated by Django 2.2 on 2021-02-19 08:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Permission Group',
                'verbose_name_plural': 'Permission Groups',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True, verbose_name='Id')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('type', models.CharField(choices=[('organizational', 'Organizational'), ('internal', 'Internal')], max_length=100, verbose_name='Type')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='permissions', to='permission.PermissionGroup', verbose_name='Group')),
            ],
            options={
                'verbose_name': 'permission',
                'verbose_name_plural': 'permissions',
                'ordering': ('group__name', 'id'),
            },
        ),
        migrations.CreateModel(
            name='InternalRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, unique=True, verbose_name='Name')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('permissions', models.ManyToManyField(blank=True, to='permission.Permission', verbose_name='Permissions')),
            ],
            options={
                'verbose_name': 'Internal Role',
                'verbose_name_plural': 'Internal Roles',
            },
        ),
    ]