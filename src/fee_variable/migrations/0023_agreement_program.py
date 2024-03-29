# Generated by Django 2.2 on 2022-01-10 11:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0022_qrcodevariable'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agreement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
                ('box_source_file_id', models.CharField(max_length=255, unique=True, verbose_name='Box Source File Id')),
            ],
            options={
                'verbose_name': 'Agreement',
                'verbose_name_plural': 'Agreements',
            },
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
                ('agreement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='program_set', to='fee_variable.Agreement', verbose_name='Agreement')),
            ],
            options={
                'verbose_name': 'Program',
                'verbose_name_plural': 'Programs',
            },
        ),
    ]
