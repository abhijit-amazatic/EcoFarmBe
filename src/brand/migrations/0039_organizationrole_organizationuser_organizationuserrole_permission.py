# Generated by Django 2.2 on 2020-12-10 11:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brand', '0038_auto_20201202_0817'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_user', to='brand.Organization', verbose_name='Organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_user', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Organization User',
                'verbose_name_plural': 'Organization Users',
                'unique_together': {('organization', 'user')},
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('codename', models.CharField(choices=[('orders', (('create_order', 'Create Order'), ('sign_order', 'Sign Order'))), ('Profile', (('view_profile', 'View Profile'),)), ('Compliance', (('view_license', 'View License'),)), ('Marketplace', (('view_pricing', 'View Pricing'), ('view_labtest', 'View Lab Test'))), ('Billing & Accounting', (('view_bills', 'View Bills'),))], max_length=100, unique=True, verbose_name='codename')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('group', models.CharField(choices=[('orders', 'orders'), ('profile', 'Profile'), ('comliance', 'Compliance'), ('marketplce', 'Marketplace'), ('billing_and_accounting', 'Billing & Accounting')], default='', editable=False, max_length=100, verbose_name='Group')),
            ],
            options={
                'verbose_name': 'permission',
                'verbose_name_plural': 'permissions',
                'ordering': ('group', 'codename'),
            },
        ),
        migrations.CreateModel(
            name='OrganizationRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=60, verbose_name='Name')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='brand.Organization', verbose_name='Organization')),
                ('permissions', models.ManyToManyField(blank=True, to='brand.Permission', verbose_name='Permissions')),
            ],
            options={
                'verbose_name': 'Organization Role',
                'verbose_name_plural': 'Organization Roles',
                'unique_together': {('organization', 'name')},
            },
        ),
        migrations.CreateModel(
            name='OrganizationUserRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('licenses', models.ManyToManyField(to='brand.License', verbose_name='Licenses')),
                ('organization_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_user_role', to='brand.OrganizationUser', verbose_name='Organization User')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_user_role', to='brand.OrganizationRole', verbose_name='Organization Role')),
            ],
            options={
                'verbose_name': 'Organization User Role',
                'verbose_name_plural': 'Organization User Roles',
                'unique_together': {('organization_user', 'role')},
            },
        ),
    ]
