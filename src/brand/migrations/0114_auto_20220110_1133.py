# Generated by Django 2.2 on 2022-01-10 11:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fee_variable', '0023_agreement_program'),
        ('brand', '0113_auto_20211222_0707'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilecategory',
            name='default_program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profile_category_default_set', to='fee_variable.Program', verbose_name='Default Program'),
        ),
        migrations.AddField(
            model_name='profilecategory',
            name='programs',
            field=models.ManyToManyField(blank=True, related_name='profile_category_set', to='fee_variable.Program', verbose_name='Programs'),
        ),
        migrations.AlterField(
            model_name='profilecategory',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
